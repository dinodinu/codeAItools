package com.calendar.srirangam

import android.content.res.AssetManager
import java.time.LocalDate
import java.time.Month

/**
 * Scans assets for month folders (e.g. jan'26) containing day images (e.g. 0503.jpg).
 */
class CalendarRepository(private val assets: AssetManager) {

    data class CalendarEntry(val date: LocalDate, val assetPath: String)

    private val monthMap = mapOf(
        "jan" to 1, "feb" to 2, "mar" to 3, "apr" to 4,
        "may" to 5, "jun" to 6, "jul" to 7, "aug" to 8,
        "sep" to 9, "oct" to 10, "nov" to 11, "dec" to 12
    )

    private val folderRegex = Regex("^([a-zA-Z]{3})'(\\d{2})$")
    private val fileRegex = Regex("^(\\d{2})(\\d{2}).*\\.(jpg|jpeg|png|bmp|webp|gif)$", RegexOption.IGNORE_CASE)

    /** Sorted list of all available dates. */
    val dates: List<LocalDate>

    /** Map from date to its first image asset path. */
    val byDate: Map<LocalDate, String>

    /** Sorted list of distinct (year, month) pairs. */
    val monthOrder: List<Pair<Int, Int>>

    /** Map from (year, month) to list of indices in [dates]. */
    val monthToDateIndices: Map<Pair<Int, Int>, List<Int>>

    init {
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
