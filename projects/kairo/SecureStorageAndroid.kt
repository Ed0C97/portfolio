// Portfolio excerpt, adapted. Android `actual` for SecureStorage.
//
// EncryptedSharedPreferences + AES-256 MasterKey is the standard AndroidX
// Security Crypto pattern (project pins 0.1.0-beta). Both are slated for
// deprecation in a later AndroidX release, so expect to swap the API then.
package com.kairo.shared.platform

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

actual class SecureStorage actual constructor() {

    // lazy so the keystore-backed prefs are built once, on first access
    private val prefs: SharedPreferences by lazy {
        val context = appContext
            ?: error("SecureStorage not initialized. Call SecureStorage.init(context) in Application.onCreate()")

        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        EncryptedSharedPreferences.create(
            context,
            "app_secure_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    actual fun save(key: String, value: String) {
        prefs.edit().putString(key, value).apply()
    }

    actual fun get(key: String): String? {
        return prefs.getString(key, null)
    }

    actual fun delete(key: String) {
        prefs.edit().remove(key).apply()
    }

    actual fun clear() {
        prefs.edit().clear().apply()
    }

    companion object {
        @Volatile
        private var appContext: Context? = null

        /** Stash the application context. Call once from Application.onCreate(), before any storage access. */
        fun init(context: Context) {
            appContext = context.applicationContext
        }
    }
}
