// Portfolio excerpt, adapted. iOS `actual` for SecureStorage: Keychain via
// Kotlin/Native cinterop with Security.framework. Trimmed to the storage surface.
//
// Kotlin/Native rejects bare `as` casts across the CoreFoundation/Foundation
// toll-free bridge, so Keychain queries are built as real CFDictionary via
// CFDictionaryCreate with the Security CFString constants. Foundation values
// (NSString/NSData) cross as CFTypeRef through CFBridgingRetain and are released
// after each call.
package com.kairo.shared.platform

import kotlinx.cinterop.*
import platform.CoreFoundation.*
import platform.Foundation.*
import platform.Security.*
import platform.darwin.UInt8Var

@OptIn(ExperimentalForeignApi::class)
actual class SecureStorage actual constructor() {

    private val service = "com.example.app" // illustrative; real builds use the bundle id

    /**
     * Build a CFDictionary from key/value CFTypeRef pairs.
     *
     * Caller owns every retained value in [pairs]; CFDictionary takes its own
     * references, so releasing the originals afterward is safe.
     */
    private fun cfDictionary(vararg pairs: Pair<CFStringRef?, CFTypeRef?>): CFDictionaryRef? = memScoped {
        val n = pairs.size
        val keys = allocArray<CFTypeRefVar>(n)
        val values = allocArray<CFTypeRefVar>(n)
        pairs.forEachIndexed { i, (k, v) ->
            keys[i] = k
            values[i] = v
        }
        CFDictionaryCreate(
            allocator = kCFAllocatorDefault,
            keys = keys.reinterpret(),
            values = values.reinterpret(),
            numValues = n.toLong(),
            keyCallBacks = kCFTypeDictionaryKeyCallBacks.ptr,
            valueCallBacks = kCFTypeDictionaryValueCallBacks.ptr
        )
    }

    private fun Any.cfRetained(): CFTypeRef? = CFBridgingRetain(this)

    private fun baseQueryPairs(key: String): Array<Pair<CFStringRef?, CFTypeRef?>> = arrayOf(
        kSecClass to kSecClassGenericPassword,
        kSecAttrService to (service as NSString).cfRetained(),
        kSecAttrAccount to (key as NSString).cfRetained()
    )

    private fun release(pairs: Array<Pair<CFStringRef?, CFTypeRef?>>) {
        // only the CFBridgingRetain'd values (NSString/NSData bridges) get released here.
        // kSec* constants are process-global; releasing one is a crash.
        pairs.forEach { (key, value) ->
            if (key == kSecAttrService || key == kSecAttrAccount ||
                key == kSecValueData
            ) {
                value?.let { CFRelease(it) }
            }
        }
    }

    actual fun save(key: String, value: String) {
        val data = value.encodeToByteArray().toNSData()

        // SecItemAdd fails with errSecDuplicateItem if the key exists, so delete first
        val deletePairs = baseQueryPairs(key)
        cfDictionary(*deletePairs)?.let { q ->
            SecItemDelete(q)
            CFRelease(q)
        }
        release(deletePairs)

        val addPairs = baseQueryPairs(key) + arrayOf(
            kSecValueData to data.cfRetained(),
            kSecAttrAccessible to kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        )
        cfDictionary(*addPairs)?.let { q ->
            val status = SecItemAdd(q, null)
            CFRelease(q)
            // status check elided in this excerpt; production logs non-success via Kermit
        }
        release(addPairs)
    }

    actual fun get(key: String): String? {
        val pairs = baseQueryPairs(key) + arrayOf(
            kSecReturnData to kCFBooleanTrue,
            kSecMatchLimit to kSecMatchLimitOne
        )
        val query = cfDictionary(*pairs) ?: run { release(pairs); return null }

        return memScoped {
            val resultPtr = alloc<CFTypeRefVar>()
            val status = SecItemCopyMatching(query, resultPtr.ptr)
            CFRelease(query)
            release(pairs)
            if (status == errSecSuccess) {
                val cfData = resultPtr.value
                // SecItemCopyMatching hands back a +1 CFData; CFBridgingRelease takes that ref
                val nsData = cfData?.let { CFBridgingRelease(it) as? NSData }
                nsData?.let { it.toByteArray().decodeToString() }
            } else {
                null
            }
        }
    }

    actual fun delete(key: String) {
        val pairs = baseQueryPairs(key)
        cfDictionary(*pairs)?.let { q ->
            SecItemDelete(q)
            CFRelease(q)
        }
        release(pairs)
    }

    actual fun clear() {
        // service-scoped query with no account matches every item we wrote
        val servicePair = arrayOf(
            kSecClass to kSecClassGenericPassword,
            kSecAttrService to (service as NSString).cfRetained()
        )
        cfDictionary(*servicePair)?.let { q ->
            SecItemDelete(q)
            CFRelease(q)
        }
        servicePair.forEach { (k, v) -> if (k == kSecAttrService) v?.let { CFRelease(it) } }
    }
}

@OptIn(ExperimentalForeignApi::class)
private fun ByteArray.toNSData(): NSData = usePinned { pinned ->
    if (isEmpty()) return NSData()
    NSData.create(bytes = pinned.addressOf(0), length = size.toULong())
}

@OptIn(ExperimentalForeignApi::class)
private fun NSData.toByteArray(): ByteArray {
    val size = length.toInt()
    if (size == 0) return ByteArray(0)
    val rawBytes = bytes ?: return ByteArray(0)
    val src = rawBytes.reinterpret<UInt8Var>()
    return ByteArray(size) { i -> src[i].toByte() }
}
