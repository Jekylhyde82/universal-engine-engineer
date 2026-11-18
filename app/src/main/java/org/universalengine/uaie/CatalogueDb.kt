package org.universalengine.uaie

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

data class CatalogueItem(
    val id: Long,
    val name: String,
    val mime: String,
    val size: Long,
    val sha256: String,
    val storedName: String,
    val sourceUri: String?,
    val importedAt: Long
)

class CatalogueDb(context: Context) : SQLiteOpenHelper(context, "uaie-catalogue.db", null, 2) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("""CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL,
            sha256 TEXT NOT NULL UNIQUE, stored_name TEXT NOT NULL,
            source_uri TEXT, imported_at INTEGER NOT NULL
        )""".trimIndent())
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        if (oldVersion < 2) {
            db.execSQL("ALTER TABLE items ADD COLUMN source_uri TEXT")
            db.execSQL("ALTER TABLE items ADD COLUMN imported_at INTEGER NOT NULL DEFAULT 0")
        }
    }

    @Synchronized
    fun insert(name: String, mime: String, size: Long, sha256: String, storedName: String, sourceUri: String): Long {
        val values = ContentValues().apply {
            put("name", name); put("mime", mime); put("size", size)
            put("sha256", sha256); put("stored_name", storedName)
            put("source_uri", sourceUri); put("imported_at", System.currentTimeMillis())
        }
        return writableDatabase.insertOrThrow("items", null, values)
    }

    @Synchronized
    fun containsHash(hash: String): Boolean =
        readableDatabase.rawQuery("SELECT 1 FROM items WHERE sha256 = ? LIMIT 1", arrayOf(hash)).use { it.moveToFirst() }

    @Synchronized
    fun totalBytes(): Long =
        readableDatabase.rawQuery("SELECT COALESCE(SUM(size),0) FROM items", null).use {
            if (it.moveToFirst()) it.getLong(0) else 0L
        }

    @Synchronized
    fun all(): List<CatalogueItem> {
        val result = mutableListOf<CatalogueItem>()
        readableDatabase.rawQuery(
            "SELECT id,name,mime,size,sha256,stored_name,source_uri,imported_at FROM items ORDER BY id DESC", null
        ).use { c ->
            while (c.moveToNext()) result += CatalogueItem(
                c.getLong(0), c.getString(1), c.getString(2), c.getLong(3),
                c.getString(4), c.getString(5), if (c.isNull(6)) null else c.getString(6), c.getLong(7)
            )
        }
        return result
    }

    @Synchronized
    fun delete(id: Long): CatalogueItem? {
        val item = all().firstOrNull { it.id == id } ?: return null
        writableDatabase.delete("items", "id = ?", arrayOf(id.toString()))
        return item
    }
}
