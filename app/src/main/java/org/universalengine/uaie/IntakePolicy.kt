package org.universalengine.uaie

internal object IntakePolicy {
    const val MAX_FILE_BYTES: Long = 10L * 1024L * 1024L
    const val MAX_CATALOGUE_BYTES: Long = 100L * 1024L * 1024L

    fun checkSize(totalBytes: Long) {
        require(totalBytes >= 0L) { "File size cannot be negative." }
        require(totalBytes <= MAX_FILE_BYTES) { "File exceeds the 10 MiB intake limit." }
    }

    fun checkQuota(currentBytes: Long, incomingBytes: Long) {
        require(currentBytes >= 0L && incomingBytes >= 0L) { "Storage sizes cannot be negative." }
        require(incomingBytes <= MAX_CATALOGUE_BYTES - currentBytes) {
            "Local catalogue storage limit reached (100 MiB). Delete an item before importing more."
        }
    }
}

internal object ContentHash {
    fun toHex(bytes: ByteArray): String =
        bytes.joinToString("") { byte -> "%02x".format(byte.toInt() and 0xff) }
}
