package com.empresa.levantamiento.ui.capture

import android.Manifest
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.core.content.FileProvider
import java.io.File

/**
 * Captura de fotografía real con la cámara del dispositivo (RF-MOV-08).
 *
 * Usa FileProvider + ActivityResultContracts.TakePicture para obtener la imagen
 * a resolución completa en un archivo temporal; al confirmarse, entrega los
 * bytes al llamador (que los pasa a PhotoManager para comprimir, hashear y
 * sellar la metadata de posición/fecha). Solicita el permiso de cámara si falta.
 */
class PhotoCaptureController(
    private val launchPermission: () -> Unit,
    private val launchCamera: () -> Unit,
    private val hasPermission: () -> Boolean,
) {
    fun capture() {
        if (hasPermission()) launchCamera() else launchPermission()
    }
}

@Composable
fun rememberPhotoCapture(onCaptured: (ByteArray) -> Unit): PhotoCaptureController {
    val context = androidx.compose.ui.platform.LocalContext.current
    val tempFile = remember { File(context.cacheDir, "capture_tmp.jpg") }
    val uri = remember {
        FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", tempFile)
    }

    val cameraLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.TakePicture()
    ) { success ->
        if (success && tempFile.exists()) {
            onCaptured(tempFile.readBytes())
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) cameraLauncher.launch(uri)
    }

    fun hasCameraPermission(): Boolean =
        androidx.core.content.ContextCompat.checkSelfPermission(
            context, Manifest.permission.CAMERA
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED

    return remember {
        PhotoCaptureController(
            launchPermission = { permissionLauncher.launch(Manifest.permission.CAMERA) },
            launchCamera = { cameraLauncher.launch(uri) },
            hasPermission = ::hasCameraPermission,
        )
    }
}
