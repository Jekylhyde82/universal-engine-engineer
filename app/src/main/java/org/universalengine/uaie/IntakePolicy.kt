package org.universalengine.uaie

internal object IntakePolicy {
    const val MAX_FILE_BYTES: Long = 10L * 1024L * 1024L

    fun checkSize(totalBytes: Long) {
        require(totalBytes >= 0L) { "File size cannot be negative." }
        require(totalBytes <= MAX_FILE_BYTES) { "File exceeds the 10 MiB intake limit." }
    }
}

internal object ContentHash {
    fun toHex(bytes: ByteArray): String =
        bytes.joinToString("") { byte -> "%02x".format(byte.toInt() and 0xff) }
}
