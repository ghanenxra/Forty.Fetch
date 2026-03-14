package com.fortyfetch.mobile

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

private const val BASE_URL = "http://10.0.2.2:8000/"

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                DownloadScreen()
            }
        }
    }
}

data class StartDownloadRequest(val url: String, val quality: String)
data class StartDownloadResponse(val job_id: String)

data class JobStatusResponse(
    val job_id: String,
    val status: String,
    val progress: Float,
    val speed: String,
    val eta: String,
    val message: String,
    val file_name: String?
)

interface FortyFetchApi {
    @POST("downloads")
    suspend fun startDownload(@Body request: StartDownloadRequest): StartDownloadResponse

    @GET("downloads/{jobId}")
    suspend fun getStatus(@Path("jobId") jobId: String): JobStatusResponse
}

private val api: FortyFetchApi by lazy {
    Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(OkHttpClient.Builder().build())
        .addConverterFactory(GsonConverterFactory.create())
        .build()
        .create(FortyFetchApi::class.java)
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun DownloadScreen() {
    val scope = rememberCoroutineScope()
    val qualities = listOf(
        "360p 60fps",
        "480p 60fps",
        "720p 60fps",
        "1080p 60fps",
        "1440p 60fps",
        "2160p 60fps (4K)",
        "4320p 60fps (8K)",
        "MP3 (Audio)",
    )

    var url by remember { mutableStateOf("") }
    var quality by remember { mutableStateOf("1080p 60fps") }
    var dropdownOpen by remember { mutableStateOf(false) }
    var statusText by remember { mutableStateOf("Ready") }
    var speedText by remember { mutableStateOf("") }
    var progress by remember { mutableStateOf(0f) }
    var activeJobId by remember { mutableStateOf<String?>(null) }
    var working by remember { mutableStateOf(false) }

    LaunchedEffect(activeJobId) {
        val id = activeJobId ?: return@LaunchedEffect
        while (true) {
            runCatching { api.getStatus(id) }
                .onSuccess { response ->
                    progress = response.progress / 100f
                    speedText = listOf(response.speed, response.eta)
                        .filter { it.isNotBlank() }
                        .joinToString(" | ")
                    statusText = when (response.status) {
                        "completed" -> "Completed: ${response.file_name ?: "done"}"
                        "failed" -> "Failed: ${response.message}"
                        else -> response.message
                    }

                    if (response.status == "completed" || response.status == "failed") {
                        working = false
                        activeJobId = null
                        return@LaunchedEffect
                    }
                }
                .onFailure {
                    statusText = "Connection error: ${it.message ?: "unknown"}"
                    working = false
                    activeJobId = null
                    return@LaunchedEffect
                }

            delay(1000)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        TopAppBar(title = { Text("FortyFetch Mobile") })

        OutlinedTextField(
            value = url,
            onValueChange = { url = it },
            modifier = Modifier.fillMaxWidth(),
            label = { Text("YouTube URL") },
            singleLine = true,
        )

        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Text("Quality: $quality")
            TextButton(onClick = { dropdownOpen = true }) {
                Text("Choose")
            }
            DropdownMenu(expanded = dropdownOpen, onDismissRequest = { dropdownOpen = false }) {
                qualities.forEach { option ->
                    DropdownMenuItem(
                        text = { Text(option) },
                        onClick = {
                            quality = option
                            dropdownOpen = false
                        }
                    )
                }
            }
        }

        Button(
            onClick = {
                if (url.isBlank()) {
                    statusText = "Enter a URL first"
                    return@Button
                }
                working = true
                statusText = "Starting download"
                progress = 0f

                scope.launch {
                    runCatching { api.startDownload(StartDownloadRequest(url, quality)) }
                        .onSuccess { activeJobId = it.job_id }
                        .onFailure {
                            statusText = "Start failed: ${it.message ?: "unknown"}"
                            working = false
                        }
                }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = !working,
        ) {
            Text(if (working) "Working..." else "Start Fetch")
        }

        LinearProgressIndicator(progress = { progress }, modifier = Modifier.fillMaxWidth())
        Text("${(progress * 100).toInt()}%")
        Text(statusText)
        if (speedText.isNotBlank()) Text(speedText)

        if (working) {
            CircularProgressIndicator()
        }

        Text(
            text = "Backend URL: $BASE_URL",
            style = MaterialTheme.typography.bodySmall,
        )
    }
}
