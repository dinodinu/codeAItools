package com.example.deccanheraldepaper

import android.Manifest
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.app.DatePickerDialog
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.MediaStore
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import android.view.View
import android.widget.ArrayAdapter
import com.example.deccanheraldepaper.databinding.ActivityMainBinding
import com.tom_roush.pdfbox.android.PDFBoxResourceLoader
import com.tom_roush.pdfbox.multipdf.PDFMergerUtility
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.IOException
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import java.util.Locale
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    companion object {
        private const val NOTIFICATION_CHANNEL_ID = "download_status"
        private const val NOTIFICATION_ID = 1001
    }

    private lateinit var binding: ActivityMainBinding
    private val repo by lazy { EpaperRepository() }
    private val requestNotificationPermission = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        PDFBoxResourceLoader.init(applicationContext)

        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        setSupportActionBar(binding.toolbar)

        binding.dateEditText.setText(LocalDate.now().toString())
        binding.editionEditText.setText("bengaluru")
        setupDatePicker()
        createNotificationChannel()
        requestNotificationPermissionIfRequired()
        loadEditionSuggestions()

        binding.downloadButton.setOnClickListener {
            startDownload()
        }

        binding.dateInputLayout.setEndIconOnClickListener {
            showDatePicker()
        }
    }

    private fun startDownload() {
        val dateStr = binding.dateEditText.text?.toString()?.trim().orEmpty()
        val editionQuery = binding.editionEditText.text?.toString()?.trim().orEmpty()

        if (!isValidDate(dateStr)) {
            binding.dateInputLayout.error = "Use YYYY-MM-DD"
            return
        }
        binding.dateInputLayout.error = null

        val normalizedEdition = if (editionQuery.isBlank()) "bengaluru" else editionQuery

        binding.downloadButton.isEnabled = false
        binding.progressBar.visibility = View.VISIBLE
        binding.statusTextView.text = "Starting..."

        lifecycleScope.launch {
            try {
                val result = withContext(Dispatchers.IO) {
                    repo.downloadAndMerge(
                        context = this@MainActivity,
                        dateStr = dateStr,
                        editionQuery = normalizedEdition
                    ) { logLine ->
                        runOnUiThread {
                            appendStatus(logLine)
                        }
                    }
                }

                appendStatus("Done: ${result.fileName}")
                appendStatus("Saved to Downloads")
                appendStatus("Main pages: ${result.mainCount}, Annexures: ${result.annexureCount}")
                showToast("Saved ${result.fileName}")
                showCompletionNotification(result)
            } catch (e: Exception) {
                appendStatus("Error: ${e.message ?: "Unknown error"}")
                showToast("Failed: ${e.message ?: "Unknown error"}")
            } finally {
                binding.downloadButton.isEnabled = true
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun setupDatePicker() {
        binding.dateEditText.setOnClickListener {
            showDatePicker()
        }
        binding.dateEditText.setOnFocusChangeListener { _, hasFocus ->
            if (hasFocus) {
                showDatePicker()
            }
        }
    }

    private fun showDatePicker() {
        val currentDate = parseDateOrToday(binding.dateEditText.text?.toString().orEmpty())
        val picker = DatePickerDialog(
            this,
            { _, year, month, dayOfMonth ->
                val selected = LocalDate.of(year, month + 1, dayOfMonth)
                binding.dateEditText.setText(selected.toString())
            },
            currentDate.year,
            currentDate.monthValue - 1,
            currentDate.dayOfMonth
        )
        picker.show()
    }

    private fun parseDateOrToday(dateStr: String): LocalDate {
        return try {
            LocalDate.parse(dateStr, DateTimeFormatter.ISO_LOCAL_DATE)
        } catch (_: DateTimeParseException) {
            LocalDate.now()
        }
    }

    private fun loadEditionSuggestions() {
        lifecycleScope.launch {
            try {
                val editions = withContext(Dispatchers.IO) {
                    repo.fetchEditionSuggestions()
                }
                val displayItems = editions
                    .map { "${it.name} (#${it.editionNumber})" }
                    .distinct()
                val adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_list_item_1, displayItems)
                binding.editionEditText.setAdapter(adapter)
                binding.editionEditText.setOnItemClickListener { _, _, position, _ ->
                    val selected = displayItems[position]
                    val cleanName = selected.substringBefore(" (#")
                    binding.editionEditText.setText(cleanName, false)
                }
                appendStatus("Loaded ${displayItems.size} edition suggestion(s)")
            } catch (e: Exception) {
                appendStatus("Could not load edition suggestions: ${e.message ?: "unknown error"}")
            }
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                getString(R.string.notif_channel_name),
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = getString(R.string.notif_channel_desc)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun requestNotificationPermissionIfRequired() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val granted = ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) {
                requestNotificationPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    private fun showCompletionNotification(result: DownloadResult) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val granted = ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) {
                return
            }
        }

        val openIntent = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(result.outputUri, "application/pdf")
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            Intent.createChooser(openIntent, "Open merged PDF"),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_download_done)
            .setContentTitle(getString(R.string.notif_title))
            .setContentText(getString(R.string.notif_open_pdf))
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        NotificationManagerCompat.from(this).notify(NOTIFICATION_ID, notification)
    }

    private fun appendStatus(line: String) {
        val existing = binding.statusTextView.text?.toString().orEmpty()
        binding.statusTextView.text = if (existing.isBlank()) line else "$existing\n$line"
    }

    private fun showToast(text: String) {
        Toast.makeText(this, text, Toast.LENGTH_LONG).show()
    }

    private fun isValidDate(dateStr: String): Boolean {
        return try {
            LocalDate.parse(dateStr, DateTimeFormatter.ISO_LOCAL_DATE)
            true
        } catch (_: DateTimeParseException) {
            false
        }
    }
}

data class Edition(
    val id: Int,
    val editionNumber: Int,
    val name: String,
    val shortCode: String,
    val region: String
)

data class PageEntry(
    val displayName: String,
    val pdfUrl: String
)

data class DownloadResult(
    val outputUri: Uri,
    val fileName: String,
    val mainCount: Int,
    val annexureCount: Int
)

class EpaperRepository {

    companion object {
        private const val API_BASE = "https://api-epaper-prod.deccanherald.com"
        private const val PUBLISHER = "DH"

        private val ANNEXURE_KEYWORDS = listOf(
            "supplement", "annexure", "annex", "pullout", "tabloid",
            "extra", "special", "magazine", "metrolife", "leisurefolio"
        )
    }

    private val client: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .retryOnConnectionFailure(true)
        .build()

    suspend fun downloadAndMerge(
        context: Context,
        dateStr: String,
        editionQuery: String,
        logger: (String) -> Unit
    ): DownloadResult {
        logger("Fetching editions...")
        val editions = fetchEditions()
        val edition = resolveEdition(editions, editionQuery)
            ?: throw IllegalArgumentException("Edition '$editionQuery' not found")

        logger("Edition: ${edition.name} (#${edition.editionNumber})")
        logger("Fetching edition metadata...")
        val editionData = fetchEditionData(dateStr, edition.editionNumber)
        val (mainPages, annexures) = extractPages(editionData)

        if (mainPages.isEmpty() && annexures.isEmpty()) {
            throw IllegalStateException("No pages found for $dateStr")
        }

        logger("Found ${mainPages.size} main page(s), ${annexures.size} annexure(s)")

        val tmpDir = File(context.cacheDir, "dh_pages_${System.currentTimeMillis()}")
        if (!tmpDir.exists() && !tmpDir.mkdirs()) {
            throw IOException("Could not create temp directory")
        }

        val downloadedMain = mutableListOf<File>()
        val downloadedAnnexure = mutableListOf<File>()

        try {
            mainPages.forEachIndexed { index, page ->
                logger("Downloading main ${index + 1}/${mainPages.size}: ${page.displayName}")
                val file = File(tmpDir, "page_${(index + 1).toString().padStart(3, '0')}.pdf")
                if (downloadPdf(page.pdfUrl, file)) {
                    downloadedMain.add(file)
                }
            }

            annexures.forEachIndexed { index, page ->
                logger("Downloading annexure ${index + 1}/${annexures.size}: ${page.displayName}")
                val file = File(tmpDir, "annexure_${(index + 1).toString().padStart(3, '0')}.pdf")
                if (downloadPdf(page.pdfUrl, file)) {
                    downloadedAnnexure.add(file)
                }
            }

            val allPages = downloadedMain + downloadedAnnexure
            if (allPages.isEmpty()) {
                throw IllegalStateException("No PDFs downloaded successfully")
            }

            val outputName = "DeccanHerald_${edition.name.replace(" ", "_")}_${dateStr}.pdf"
            logger("Merging ${allPages.size} PDF(s)...")

            val mergedFile = File(tmpDir, "merged_output.pdf")
            mergePdfs(allPages, mergedFile)

            val outputUri = saveToDownloads(context, outputName, mergedFile)
            return DownloadResult(
                outputUri = outputUri,
                fileName = outputName,
                mainCount = downloadedMain.size,
                annexureCount = downloadedAnnexure.size
            )
        } finally {
            tmpDir.listFiles()?.forEach { it.delete() }
            tmpDir.delete()
        }
    }

    suspend fun fetchEditionSuggestions(): List<Edition> {
        return fetchEditions()
    }

    private fun fetchEditions(): List<Edition> {
        val url = "$API_BASE/epaper/editions?publisher=$PUBLISHER"
        val jsonString = getWithRetries(url)
        val root = JSONArray(jsonString)

        val result = mutableListOf<Edition>()
        for (i in 0 until root.length()) {
            val group = root.getJSONObject(i)
            val parent = group.optString("parent_edition")
            val editions = group.optJSONArray("editions") ?: JSONArray()
            for (j in 0 until editions.length()) {
                val ed = editions.getJSONObject(j)
                result.add(
                    Edition(
                        id = ed.optInt("id"),
                        editionNumber = ed.optInt("edition_number"),
                        name = ed.optString("edition_name"),
                        shortCode = ed.optString("edition_short_code"),
                        region = parent
                    )
                )
            }
        }

        return result
    }

    private fun resolveEdition(editions: List<Edition>, query: String): Edition? {
        val q = query.lowercase(Locale.getDefault()).trim()

        val asNumber = q.toIntOrNull()
        if (asNumber != null) {
            editions.firstOrNull { it.editionNumber == asNumber || it.id == asNumber }?.let { return it }
        }

        editions.firstOrNull { it.name.lowercase(Locale.getDefault()) == q }?.let { return it }
        editions.firstOrNull { it.shortCode.lowercase(Locale.getDefault()) == q }?.let { return it }
        editions.firstOrNull { it.name.lowercase(Locale.getDefault()).contains(q) }?.let { return it }

        return null
    }

    private fun fetchEditionData(dateStr: String, editionNumber: Int): JSONObject {
        val apiDate = dateStr.replace("-", "")
        val url = "$API_BASE/epaper/data?date=$apiDate&edition=$editionNumber&publisher=$PUBLISHER"

        val request = Request.Builder()
            .url(url)
            .header("User-Agent", userAgent())
            .header("Accept", "application/json, */*")
            .header("Origin", "https://epaper.deccanherald.com")
            .header("Referer", "https://epaper.deccanherald.com/")
            .build()

        client.newCall(request).execute().use { response ->
            when (response.code) {
                403 -> throw IllegalStateException("Access denied. Non-Bengaluru editions may need subscription")
                404 -> throw IllegalStateException("No edition found for $dateStr")
            }

            if (!response.isSuccessful) {
                throw IOException("Failed to fetch edition data: HTTP ${response.code}")
            }

            val body = response.body?.string().orEmpty()
            if (body.isBlank()) {
                throw IOException("Empty response from edition API")
            }
            return JSONObject(body)
        }
    }

    private fun extractPages(editionData: JSONObject): Pair<List<PageEntry>, List<PageEntry>> {
        val dataUrlSuffix = editionData.optString("data_url_suffix")
        val sections = editionData.optJSONObject("data")?.optJSONArray("sections") ?: JSONArray()

        val mainPages = mutableListOf<PageEntry>()
        val annexures = mutableListOf<PageEntry>()

        for (i in 0 until sections.length()) {
            val section = sections.getJSONObject(i)
            val sectionId = section.optString("id")
            val sectionName = section.optString("name")
            val isAnnexureSection = sectionId != "Main" || ANNEXURE_KEYWORDS.any {
                sectionName.lowercase(Locale.getDefault()).contains(it)
            }

            val pages = section.optJSONArray("pages") ?: JSONArray()
            for (j in 0 until pages.length()) {
                val page = pages.getJSONObject(j)
                val pageNo = page.optString("pageNo", "??")
                val displayName = page.optString("displayName", "Page $pageNo")

                val pdfFile = buildPdfFile(page)
                if (pdfFile == null) {
                    continue
                }

                val entry = PageEntry(displayName = displayName, pdfUrl = dataUrlSuffix + pdfFile)
                if (isAnnexureSection) {
                    annexures.add(entry)
                } else {
                    mainPages.add(entry)
                }
            }
        }

        return mainPages to annexures
    }

    private fun buildPdfFile(page: JSONObject): String? {
        val direct = page.optString("pdfFile")
        if (direct.isNotBlank()) {
            return direct
        }

        val thumb = page.optString("imgThumbFile")
        val id = Regex("(\\d+)\\.\\w+$").find(thumb)?.groupValues?.getOrNull(1)
        return if (id.isNullOrBlank()) null else "webepaper/pdf/$id.pdf"
    }

    private fun downloadPdf(url: String, destFile: File): Boolean {
        val request = Request.Builder()
            .url(url)
            .header("User-Agent", userAgent())
            .build()

        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) {
                return false
            }

            val body = response.body ?: return false
            destFile.outputStream().use { out ->
                body.byteStream().copyTo(out)
            }

            if (destFile.length() < 500L) {
                destFile.delete()
                return false
            }

            return true
        }
    }

    private fun mergePdfs(pdfFiles: List<File>, outputFile: File) {
        val merger = PDFMergerUtility()
        pdfFiles.forEach { merger.addSource(it) }
        merger.destinationFileName = outputFile.absolutePath
        merger.mergeDocuments(null)
    }

    private fun saveToDownloads(context: Context, fileName: String, source: File): Uri {
        val values = ContentValues().apply {
            put(MediaStore.Downloads.DISPLAY_NAME, fileName)
            put(MediaStore.Downloads.MIME_TYPE, "application/pdf")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
                put(MediaStore.Downloads.IS_PENDING, 1)
            }
        }

        val collection = MediaStore.Downloads.EXTERNAL_CONTENT_URI
        val uri = context.contentResolver.insert(collection, values)
            ?: throw IOException("Unable to create output file in Downloads")

        context.contentResolver.openOutputStream(uri).use { output ->
            if (output == null) {
                throw IOException("Unable to write output PDF")
            }
            source.inputStream().use { input ->
                input.copyTo(output)
            }
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val publishValues = ContentValues().apply {
                put(MediaStore.Downloads.IS_PENDING, 0)
            }
            context.contentResolver.update(uri, publishValues, null, null)
        }

        return uri
    }

    private fun getWithRetries(url: String, maxAttempts: Int = 3): String {
        var lastError: Exception? = null
        repeat(maxAttempts) { attempt ->
            try {
                val request = Request.Builder()
                    .url(url)
                    .header("User-Agent", userAgent())
                    .header("Accept", "application/json, */*")
                    .header("Origin", "https://epaper.deccanherald.com")
                    .header("Referer", "https://epaper.deccanherald.com/")
                    .build()

                client.newCall(request).execute().use { response ->
                    if (!response.isSuccessful) {
                        throw IOException("HTTP ${response.code}")
                    }
                    val body = response.body?.string().orEmpty()
                    if (body.isBlank()) {
                        throw IOException("Empty response")
                    }
                    return body
                }
            } catch (e: Exception) {
                lastError = e
                if (attempt < maxAttempts - 1) {
                    Thread.sleep((attempt + 1) * 1000L)
                }
            }
        }
        throw IOException("Request failed after $maxAttempts attempts", lastError)
    }

    private fun userAgent(): String {
        return "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    }
}
