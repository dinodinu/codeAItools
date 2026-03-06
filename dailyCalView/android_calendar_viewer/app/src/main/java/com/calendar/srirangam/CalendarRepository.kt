package com.calendar.srirangam

import android.content.res.AssetManager
import android.net.Uri
import androidx.documentfile.provider.DocumentFile
import android.content.Context
import java.time.LocalDate

/**
 * Scans for month folders (e.g. jan'26) containing day images (e.g. 0503.jpg).
 * Supports two sources:
 *   1. Bundled assets (AssetManager)
 *   2. External folder chosen via SAF (DocumentFile URI)
 */
class CalendarRepository private constructor() {

    data class CalendarEntry(val date: LocalDate, val assetPath: String)

    private val monthMap = mapOf(
        "jan" to 1, "feb" to 2, "mar" to 3, "apr" to 4,
        "may" to 5, "jun" to 6, "jul" to 7, "aug" to 8,
        "sep" to 9, "oct" to 10, "nov" to 11, "dec" to 12
    )

    private val folderRegex = Regex("^([a-zA-Z]{3})'(\\d{2})$")
    private val fileRegex = Regex("^(\\d{2})(\\d{2}).*\\.(jpg|jpeg|png|bmp|webp|gif)$", RegexOption.IGNORE_CASE)

    /** Sorted list of all available dates. */
    var dates: List<LocalDate> = emptyList()
        private set

    /** Map from date to image path/URI string. */
    var byDate: Map<LocalDate, String> = emptyMap()
        private set

    /** Sorted list of distinct (year, month) pairs. */
    var monthOrder: List<Pair<Int, Int>> = emptyList()
        private set

    /** Map from (year, month) to list of indices in [dates]. */
    var monthToDateIndices: Map<Pair<Int, Int>, List<Int>> = emptyMap()
        private set

    /** True if images are loaded from an external folder URI. */
    var isExternalSource: Boolean = false
        private set

    constructor(assets: AssetManager) : this() {
        loadFromAssets(assets)
    }

    constructor(context: Context, treeUri: Uri) : this() {
        isExternalSource = true
        loadFromDocumentTree(context, treeUri)
    }

    private fun loadFromAssets(assets: AssetManager) {
        val entries = mutableMapOf<LocalDate, String>()

        val topLevel = assets.list("") ?: emptyArray()
        for (folder in topLevel.sorted()) {
            val folderMatch = folderRegex.matchEntire(folder) ?: continue
            val monthToken = folderMatch.groupValues[1].lowercase()
            val monthNum = monthMap[monthToken] ?: continue
            val year = 2000 + folderMatch.groupValues[2].toInt()

            val files = assets.list(folder) ?: emptyArray()
            for (file in files.sorted()) {
                val fileMatch = fileRegex.matchEntire(file) ?: continue
                val day = fileMatch.groupValues[1].toInt()
                val fileMonth = fileMatch.groupValues[2].toInt()
                if (fileMonth != monthNum) continue

                val date = try {
                    LocalDate.of(year, monthNum, day)
                } catch (_: Exception) {
                    continue
                }

                if (date !in entries) {
                    entries[date] = "$folder/$file"
                }
            }
        }

        buildIndices(entries)
    }

    private fun loadFromDocumentTree(context: Context, treeUri: Uri) {
        val entries = mutableMapOf<LocalDate, String>()
        val rootDoc = DocumentFile.fromTreeUri(context, treeUri) ?: return

        val folders = rootDoc.listFiles()
            .filter { it.isDirectory }
            .sortedBy { it.name }

        for (folderDoc in folders) {
            val folderName = folderDoc.name ?: continue
            val folderMatch = folderRegex.matchEntire(folderName) ?: continue
            val monthToken = folderMatch.groupValues[1].lowercase()
            val monthNum = monthMap[monthToken] ?: continue
            val year = 2000 + folderMatch.groupValues[2].toInt()

            val files = folderDoc.listFiles()
                .filter { it.isFile }
                .sortedBy { it.name }

            for (fileDoc in files) {
                val fileName = fileDoc.name ?: continue
                val fileMatch = fileRegex.matchEntire(fileName) ?: continue
                val day = fileMatch.groupValues[1].toInt()
                val fileMonth = fileMatch.groupValues[2].toInt()
                if (fileMonth != monthNum) continue

                val date = try {
                    LocalDate.of(year, monthNum, day)
                } catch (_: Exception) {
                    continue
                }

                if (date !in entries) {
                    entries[date] = fileDoc.uri.toString()
                }
            }
        }

        buildIndices(entries)
    }

    private fun buildIndices(entries: MutableMap<LocalDate, String>) {
        byDate = entries.toSortedMap()
        dates = byDate.keys.toList()

        val monthIndices = mutableMapOf<Pair<Int, Int>, MutableList<Int>>()
        for ((idx, d) in dates.withIndex()) {
            monthIndices.getOrPut(d.year to d.monthValue) { mutableListOf() }.add(idx)
        }
        monthToDateIndices = monthIndices
        monthOrder = monthIndices.keys.sorted()
    }

    fun hasData(): Boolean = dates.isNotEmpty()

    /** Find the index of the date nearest to [target]. */
    fun nearestIndex(target: LocalDate): Int {
        if (dates.isEmpty()) return -1
        val pos = dates.binarySearch(target).let { if (it < 0) -(it + 1) else it }
        return when {
            pos == 0 -> 0
            pos >= dates.size -> dates.size - 1
            else -> {
                val before = dates[pos - 1]
                val after = dates[pos]
                if (java.time.temporal.ChronoUnit.DAYS.between(before, target) <=
                    java.time.temporal.ChronoUnit.DAYS.between(target, after)
                ) pos - 1 else pos
            }
        }
    }
}
