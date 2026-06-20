// Portfolio excerpt, adapted.
package com.kairo.shared.platform

enum class BiometricResult { SUCCESS, CANCELLED, FAILED, NOT_AVAILABLE }
enum class BiometricType { FACE_ID, TOUCH_ID, FINGERPRINT, NONE }

/** Credential store backed by Keychain on iOS, EncryptedSharedPreferences on Android. */
expect class SecureStorage() {
    fun save(key: String, value: String)
    fun get(key: String): String?
    fun delete(key: String)
    fun clear()
}

/** Biometric prompt: Face ID / Touch ID on iOS, BiometricPrompt on Android. */
expect class BiometricAuthenticator() {
    suspend fun authenticate(reason: String): BiometricResult
    fun isAvailable(): Boolean
    fun getBiometricType(): BiometricType
}
