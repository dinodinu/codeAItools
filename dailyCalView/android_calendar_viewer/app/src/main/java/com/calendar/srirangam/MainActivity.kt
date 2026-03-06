package com.calendar.srirangam

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.viewmodel.compose.viewModel

class MainActivity : ComponentActivity() {

    companion object {
        private const val PREFS_NAME = "calendar_config"
        private const val KEY_FOLDER_URI = "images_folder_uri"
    }

    private var uiRevision by mutableIntStateOf(0)

    private val folderPicker =
        registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri: Uri? ->
            if (uri == null) return@registerForActivityResult
            // Persist permission across reboots
            contentResolver.takePersistableUriPermission(
                uri, Intent.FLAG_GRANT_READ_URI_PERMISSION
            )
            // Save to preferences
            getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
                .edit()
                .putString(KEY_FOLDER_URI, uri.toString())
                .apply()
            // Reload with new folder
            pendingFolderUri = uri
            uiRevision++
            recreate()
        }

    private var pendingFolderUri: Uri? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val savedUriStr = getSharedPreferences(PREFS_NAME, MODE_PRIVATE)
            .getString(KEY_FOLDER_URI, null)
        val savedUri = savedUriStr?.let { Uri.parse(it) }

        setContent {
            MaterialTheme {
                val vm: CalendarViewModel = viewModel()

                // If a saved external folder URI exists, load from it
                if (savedUri != null && !vm.repo.isExternalSource) {
                    vm.loadFromExternalFolder(savedUri)
                }

                // If no data from assets or saved folder, prompt user to pick a folder
                if (!vm.repo.hasData()) {
                    FolderPromptScreen(
                        onPickFolder = { folderPicker.launch(null) },
                        onQuit = { finish() }
                    )
                } else {
                    CalendarScreen(viewModel = vm, onQuit = { finish() })
                }
            }
        }
    }
}
