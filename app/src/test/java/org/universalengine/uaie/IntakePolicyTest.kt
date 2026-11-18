package org.universalengine.uaie

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class IntakePolicyTest {
    @Test
    fun acceptsEmptyAndMaximumSizedFiles() {
        IntakePolicy.checkSize(0L)
        IntakePolicy.checkSize(IntakePolicy.MAX_FILE_BYTES)
    }

    @Test
    fun rejectsOversizedFiles() {
        assertThrows(IllegalArgumentException::class.java) {
            IntakePolicy.checkSize(IntakePolicy.MAX_FILE_BYTES + 1L)
        }
    }

    @Test
    fun rejectsNegativeSizes() {
        assertThrows(IllegalArgumentException::class.java) {
            IntakePolicy.checkSize(-1L)
        }
    }

    @Test
    fun formatsSha256BytesAsLowercaseHex() {
        assertEquals("00ff10", ContentHash.toHex(byteArrayOf(0, -1, 16)))
    }
}
