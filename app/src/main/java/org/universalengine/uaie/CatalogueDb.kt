package org.universalengine.uaie

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

data class CatalogueItem(val id: Long, val name: String, val mime: String, val size: Long, val sha256: String, val storedName: String)

class CatalogueDb(context: Context) : SQLiteOpenHelper(context, "uaie-catalogue.db", null, 1) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("""CREATE TABLE items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, mime TEXT NOT NULL, size INTEGER NOT NULL,
            sha256 TEXT NOT NULL UNIQUE, stored_name TEXT NOT NULL
        )""".trimIndent())
    }
    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        // Add explicit, versioned migrations before changing this schema.
    }
    fun insert(name: String, mime: String, size: Long, sha256: String, storedName: String) {
        val values = ContentValues().apply {
            put("name", name); put("mime", mime); put("size", size)
            put("sha256", sha256); put("stored_name", storedName)
        }
        writableDatabase.insertOrThrow("items", null, values)
    }
    fun containsHash(hash: String): Boolean =
        readableDatabase.rawQuery("SELECT 1 FROM items WHERE sha256 = ? LIMIT 1", arrayOf(hash)).use { it.moveToFirst() }
    fun all(): List<CatalogueItem> {
        val result = mutableListOf<CatalogueItem>()
        readableDatabase.rawQuery("SELECT id,name,mime,size,sha256,stored_name FROM items ORDER BY id DESC", null).use { c ->
            while (c.moveToNext()) result += CatalogueItem(c.getLong(0), c.getString(1), c.getString(2), c.getLong(3), c.getString(4), c.getString(5))
        }
        return result
    }
    fun delete(id: Long): CatalogueItem? {
        val item = all().firstOrNull { it.id == id } ?: return null
        writableDatabase.delete("items", "id = ?", arrayOf(id.toString()))
        return item
    }
}
