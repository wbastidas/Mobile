package com.empresa.levantamiento.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme

private data class ChipStyle(val bg: Color, val fg: Color, val label: String)

private fun styleFor(status: String): ChipStyle = when (status) {
    "ASSIGNED", "DOWNLOADED" -> ChipStyle(Color(0xFFDBEAFE), Color(0xFF1D4ED8), "Asignado")
    "IN_PROGRESS" -> ChipStyle(Color(0xFFFEF3C7), Color(0xFFB45309), "En ejecución")
    "SYNCING" -> ChipStyle(Color(0xFFFEF3C7), Color(0xFFB45309), "Sincronizando")
    "SYNCED", "COMPLETED" -> ChipStyle(Color(0xFFDCFCE7), Color(0xFF15803D), "Terminado")
    "WITH_ISSUES" -> ChipStyle(Color(0xFFFEF3C7), Color(0xFFB45309), "Con novedades")
    "SYNC_PENDING" -> ChipStyle(Color(0xFFFEE2E2), Color(0xFFB91C1C), "Sync pendiente")
    else -> ChipStyle(Color(0xFFF1F5F9), Color(0xFF475569), status)
}

@Composable
fun StatusChip(status: String) {
    val s = styleFor(status)
    Text(
        text = s.label,
        color = s.fg,
        style = MaterialTheme.typography.labelLarge,
        fontWeight = FontWeight.SemiBold,
        modifier = Modifier
            .background(s.bg, RoundedCornerShape(999.dp))
            .padding(horizontal = 10.dp, vertical = 3.dp),
    )
}

fun workTypeLabel(type: String): String = when (type) {
    "REVISION_RED" -> "Revisión de red (sector)"
    "ORDEN_PUNTUAL" -> "Orden puntual"
    "MANTENIMIENTO" -> "Mantenimiento / proyecto"
    else -> type
}
