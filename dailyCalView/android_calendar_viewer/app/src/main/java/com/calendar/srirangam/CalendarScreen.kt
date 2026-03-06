package com.calendar.srirangam

import android.app.DatePickerDialog
import android.content.Context
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.SubcomposeAsyncImage
import coil.request.ImageRequest
import java.time.LocalDate

@Composable
fun FolderPromptScreen(onPickFolder: () -> Unit, onQuit: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize().padding(32.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = "No calendar images found",
            fontSize = 20.sp,
            fontWeight = FontWeight.SemiBold,
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = "Select a folder containing calendar images\n(e.g. folders like jan'26 with files like 0101.jpg)",
            fontSize = 14.sp,
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(24.dp))
        Button(onClick = onPickFolder) {
            Text("Select Folder")
        }
        Spacer(modifier = Modifier.height(12.dp))
        OutlinedButton(onClick = onQuit) {
            Text("Quit")
        }
    }
}

@Composable
fun CalendarScreen(viewModel: CalendarViewModel, onQuit: () -> Unit) {
    var revision by remember { mutableIntStateOf(0) }

    val dateText = remember(revision) { viewModel.dateText }
    val statusText = remember(revision) { viewModel.statusText }
    val assetPath = remember(revision) { viewModel.currentAssetPath }

    var zoom by remember { mutableFloatStateOf(1f) }
    var offsetX by remember { mutableFloatStateOf(0f) }
    var offsetY by remember { mutableFloatStateOf(0f) }

    fun resetZoom() { zoom = 1f; offsetX = 0f; offsetY = 0f }
    fun navigate(action: () -> Unit) { action(); resetZoom(); revision++ }

    val context = LocalContext.current

    // Determine image model: content URI for external, asset path for bundled
    val imageModel = remember(revision) {
        assetPath?.let { path ->
            if (path.startsWith("content://")) {
                Uri.parse(path)
            } else {
                "file:///android_asset/$path"
            }
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        // Date header
        Text(
            text = dateText,
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp),
            textAlign = TextAlign.Center,
            fontSize = 18.sp,
            fontWeight = FontWeight.SemiBold
        )

        // Image area
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .background(Color(0xFF111111))
                .pointerInput(revision) {
                    detectTransformGestures { _, pan, gestureZoom, _ ->
                        zoom = (zoom * gestureZoom).coerceIn(0.25f, 6f)
                        offsetX += pan.x
                        offsetY += pan.y
                    }
                },
            contentAlignment = Alignment.Center
        ) {
            if (imageModel != null) {
                SubcomposeAsyncImage(
                    model = ImageRequest.Builder(context)
                        .data(imageModel)
                        .crossfade(true)
                        .build(),
                    contentDescription = "Calendar image",
                    contentScale = ContentScale.Fit,
                    modifier = Modifier
                        .fillMaxSize()
                        .graphicsLayer(
                            scaleX = zoom,
                            scaleY = zoom,
                            translationX = offsetX,
                            translationY = offsetY
                        ),
                    loading = {
                        CircularProgressIndicator(
                            modifier = Modifier.size(48.dp),
                            color = Color.White
                        )
                    },
                    error = {
                        Text("Failed to load", color = Color.White)
                    }
                )
            } else {
                Text("No image", color = Color.Gray, fontSize = 16.sp)
            }
        }

        // Navigation buttons
        NavigationBar(
            onPrevMonth = { navigate { viewModel.movePrevMonth() } },
            onPrevDay = { navigate { viewModel.movePrevDay() } },
            onGoToDate = { showDatePicker(context, viewModel.currentDate) { navigate { viewModel.goToDate(it) } } },
            onToday = { navigate { viewModel.goToToday() } },
            onNextDay = { navigate { viewModel.moveNextDay() } },
            onNextMonth = { navigate { viewModel.moveNextMonth() } },
            onZoomOut = { zoom = (zoom / 1.25f).coerceAtLeast(0.25f) },
            onFit = { resetZoom() },
            onZoomIn = { zoom = (zoom * 1.25f).coerceAtMost(6f) },
            onQuit = onQuit,
            statusText = statusText
        )
    }
}

@Composable
private fun NavigationBar(
    onPrevMonth: () -> Unit,
    onPrevDay: () -> Unit,
    onGoToDate: () -> Unit,
    onToday: () -> Unit,
    onNextDay: () -> Unit,
    onNextMonth: () -> Unit,
    onZoomOut: () -> Unit,
    onFit: () -> Unit,
    onZoomIn: () -> Unit,
    onQuit: () -> Unit,
    statusText: String
) {
    Column(modifier = Modifier.fillMaxWidth().padding(4.dp)) {
        // Row 1: Day/Month navigation
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            SmallButton("<< Month") { onPrevMonth() }
            SmallButton("< Day") { onPrevDay() }
            SmallButton("Go To") { onGoToDate() }
            SmallButton("Today") { onToday() }
            SmallButton("Day >") { onNextDay() }
            SmallButton("Month >>") { onNextMonth() }
        }

        Spacer(modifier = Modifier.height(4.dp))

        // Row 2: Zoom + status + quit
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly,
            verticalAlignment = Alignment.CenterVertically
        ) {
            SmallButton("Zoom -") { onZoomOut() }
            SmallButton("Fit") { onFit() }
            SmallButton("Zoom +") { onZoomIn() }
            Text(
                text = statusText,
                modifier = Modifier.weight(1f).padding(horizontal = 4.dp),
                textAlign = TextAlign.Center,
                fontSize = 11.sp,
                maxLines = 1
            )
            SmallButton("Quit") { onQuit() }
        }
    }
}

@Composable
private fun SmallButton(text: String, onClick: () -> Unit) {
    Button(
        onClick = onClick,
        contentPadding = PaddingValues(horizontal = 8.dp, vertical = 4.dp),
        modifier = Modifier.height(36.dp)
    ) {
        Text(text, fontSize = 11.sp, maxLines = 1)
    }
}

private fun showDatePicker(
    context: Context,
    current: LocalDate,
    onDateSelected: (LocalDate) -> Unit
) {
    DatePickerDialog(
        context,
        { _, year, month, day -> onDateSelected(LocalDate.of(year, month + 1, day)) },
        current.year,
        current.monthValue - 1,
        current.dayOfMonth
    ).show()
}
