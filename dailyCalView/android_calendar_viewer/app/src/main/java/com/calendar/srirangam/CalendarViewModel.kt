package com.calendar.srirangam

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import java.time.LocalDate
import java.time.format.DateTimeFormatter

class CalendarViewModel(application: Application) : AndroidViewModel(application) {

    val repo = CalendarRepository(application.assets)

    var currentIndex: Int = repo.nearestIndex(LocalDate.now()).coerceAtLeast(0)
        private set

    val currentDate: LocalDate
        get() = if (repo.dates.isNotEmpty()) repo.dates[currentIndex] else LocalDate.now()

    val currentAssetPath: String?
        get() = repo.byDate[currentDate]

    val dateText: String
        get() = currentDate.format(DateTimeFormatter.ofPattern("EEEE, dd MMMM yyyy"))

    val statusText: String
        get() {
            val path = currentAssetPath ?: return "No image"
            val fileName = path.substringAfterLast('/')
            return "Showing $fileName"
        }

    fun movePrevDay() {
        if (repo.dates.isEmpty()) return
        currentIndex = (currentIndex - 1 + repo.dates.size) % repo.dates.size
    }

    fun moveNextDay() {
        if (repo.dates.isEmpty()) return
        currentIndex = (currentIndex + 1) % repo.dates.size
    }

    fun movePrevMonth() = moveMonth(-1)
    fun moveNextMonth() = moveMonth(1)

    private fun moveMonth(step: Int) {
        if (repo.monthOrder.isEmpty()) return
        val cur = currentDate
        val curMonth = cur.year to cur.monthValue
        val curMonthIdx = repo.monthOrder.indexOf(curMonth)
        if (curMonthIdx < 0) return

        val targetMonthIdx = (curMonthIdx + step + repo.monthOrder.size) % repo.monthOrder.size
        val targetMonth = repo.monthOrder[targetMonthIdx]
        val targetDateIndices = repo.monthToDateIndices[targetMonth] ?: return

        // Try to keep same day-of-month.
        val sameDayIdx = targetDateIndices.firstOrNull { repo.dates[it].dayOfMonth == cur.dayOfMonth }
        currentIndex = sameDayIdx
            ?: if (step > 0) targetDateIndices.last() else targetDateIndices.first()
    }

    fun goToToday() {
        currentIndex = repo.nearestIndex(LocalDate.now()).coerceAtLeast(0)
    }

    fun goToDate(target: LocalDate) {
        currentIndex = repo.nearestIndex(target).coerceAtLeast(0)
    }
}
