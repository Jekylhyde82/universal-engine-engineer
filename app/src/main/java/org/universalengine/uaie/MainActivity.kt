package org.universalengine.uaie

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.provider.OpenableColumns
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import java.io.File
import java.security.MessageDigest
import java.util.UUID

class MainActivity : Activity() {
    private lateinit var db: CatalogueDb
    private lateinit var list: LinearLayout
    private lateinit var status: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        db = CatalogueDb(this)
        buildScreen()
        handleIncoming(intent)
        renderCatalogue()
    }
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIncoming(intent)
    }
    private fun buildScreen() {
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(20, 24, 20, 16) }
        root.addView(TextView(this).apply { text = "UAIE • Local acquisition"; textSize = 24f })
        root.addView(TextView(this).apply {
            text = "Offline-first catalogue • Imported content is stored, never executed."
            textSize = 14f; setPadding(0, 8, 0, 16)
        })
        root.addView(Button(this).apply { text = "Import file"; setOnClickListener { openPicker() } })
        status = TextView(this).apply { text = "Offline mode: local catalogue available"; textSize = 14f; setPadding(0, 8, 0, 12) }
        root.addView(status)
        val scroll = ScrollView(this)
        list = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        scroll.addView(list)
        root.addView(scroll, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f))
        setContentView(root)
    }
    private fun openPicker() {
        val picker = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE); type = "*/*"
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        startActivityForResult(picker, REQUEST_OPEN)
    }
    @Deprecated("Platform result API keeps the first build dependency-free")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_OPEN && resultCode == RESULT_OK) data?.data?.let { importUri(it) }
    }
    private fun handleIncoming(incoming: Intent?) {
        if (incoming?.action == Intent.ACTION_SEND) {
            val uri = if (android.os.Build.VERSION.SDK_INT >= 33) incoming.getParcelableExtra(Intent.EXTRA_STREAM, Uri::class.java)
            else {
                @Suppress("DEPRECATION")
                incoming.getParcelableExtra(Intent.EXTRA_STREAM)
            }
            uri?.let { importUri(it) }
        }
    }
    private fun importUri(uri: Uri) {
        status.text = "Importing selected file…"
        Thread {
            val temp = File(cacheDir, "uaie-" + UUID.randomUUID().toString() + ".part")
            try {
                val name = displayName(uri) ?: ("imported-" + System.currentTimeMillis())
                val mime = contentResolver.getType(uri) ?: "application/octet-stream"
                val digest = MessageDigest.getInstance("SHA-256")
                var total = 0L
                contentResolver.openInputStream(uri)?.use { input ->
                    temp.outputStream().buffered().use { output ->
                        val buffer = ByteArray(16 * 1024)
                        while (true) {
                            val count = input.read(buffer)
                            if (count < 0) break
                            total += count
                            IntakePolicy.checkSize(total)
                            digest.update(buffer, 0, count)
                            output.write(buffer, 0, count)
                        }
                    }
                } ?: error("Android could not open this file.")
                val hash = ContentHash.toHex(digest.digest())
                if (db.containsHash(hash)) {
                    temp.delete()
                    runOnUiThread { status.text = "Already catalogued: duplicate SHA-256." }
                    return@Thread
                }
                val storedName = hash + ".blob"
                val destination = File(filesDir, storedName)
                if (!temp.renameTo(destination)) { temp.copyTo(destination, overwrite = false); temp.delete() }
                db.insert(name, mime, total, hash, storedName)
                runOnUiThread {
                    status.text = "Imported and preserved locally • " + formatBytes(total)
                    renderCatalogue()
                }
            } catch (error: Exception) {
                temp.delete()
                runOnUiThread { status.text = "Import failed: " + (error.message ?: error.javaClass.simpleName) }
            }
        }.start()
    }
    private fun displayName(uri: Uri): String? {
        contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use {
            if (it.moveToFirst()) return it.getString(0)
        }
        return uri.lastPathSegment
    }
    private fun renderCatalogue() {
        list.removeAllViews()
        val items = db.all()
        if (items.isEmpty()) {
            list.addView(TextView(this).apply { text = "No items yet. Import a file to begin."; textSize = 15f; setPadding(0, 12, 0, 12) })
            return
        }
        items.forEach { item ->
            val card = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(12, 12, 12, 12) }
            card.addView(TextView(this).apply { text = item.name; textSize = 17f })
            card.addView(TextView(this).apply {
                text = formatBytes(item.size) + " • " + item.mime + "\nSHA-256 " + item.sha256
                textSize = 12f
            })
            card.addView(Button(this).apply {
                text = "Delete local copy"
                setOnClickListener {
                    db.delete(item.id)?.let { File(filesDir, it.storedName).delete() }
                    status.text = "Local item deleted."
                    renderCatalogue()
                }
            })
            list.addView(card)
        }
    }
    private fun formatBytes(bytes: Long): String =
        if (bytes < 1024) "$bytes B" else String.format("%.1f KiB", bytes / 1024.0)
    override fun onDestroy() { db.close(); super.onDestroy() }
    companion object { private const val REQUEST_OPEN = 4101 }
}
