package org.universalengine.uaie

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class IntakePolicyTest {
    @Test fun acceptsEmptyAndMaximumFile() {
        IntakePolicy.checkSize(0)
        IntakePolicy.checkSize(IntakePolicy.MAX_FILE_BYTES)
    }

    @Test fun rejectsOversizedFile() {
        assertThrows(IllegalArgumentException::class.java) {
            IntakePolicy.checkSize(IntakePolicy.MAX_FILE_BYTES + 1)
        }
    }

    @Test fun rejectsNegativeSize() {
        assertThrows(IllegalArgumentException::class.java) { IntakePolicy.checkSize(-1) }
    }

    @Test fun formatsSha256AsLowercaseHex() {
        assertEquals("000fff", ContentHash.toHex(byteArrayOf(0, 15, -1)))
    }

    @Test fun acceptsQuotaBoundary() {
        IntakePolicy.checkQuota(90, 10)
    }

    @Test fun rejectsQuotaOverflow() {
        assertThrows(IllegalArgumentException::class.java) {
            IntakePolicy.checkQuota(IntakePolicy.MAX_CATALOGUE_BYTES, 1)
        }
    }

    @Test fun rejectsNegativeQuotaInputs() {
        assertThrows(IllegalArgumentException::class.java) { IntakePolicy.checkQuota(-1, 0) }
    }
}
