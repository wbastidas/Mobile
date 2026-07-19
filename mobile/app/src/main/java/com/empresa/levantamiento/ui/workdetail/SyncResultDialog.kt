package com.empresa.levantamiento.ui.workdetail

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Divider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.empresa.levantamiento.core.quality.QualityIssue
import com.empresa.levantamiento.sync.SyncManager

/**
 * Resultado de la sincronización, explicado al funcionario:
 *  - Con novedades: detalle claro por elemento/regla/valor esperado (RF-MOV-09.3).
 *  - Verificada: pregunta si desea eliminar el trabajo del dispositivo; la
 *    eliminación local SOLO se ofrece tras sync completa confirmada (RF-MOV-10.3, RN-03).
 *  - Pendiente: motivo del fallo; el proceso completo se reintenta (RN-04).
 */
@Composable
fun SyncResultDialog(
    outcome: SyncManager.SyncOutcome,
    onDismiss: () -> Unit,
    onDeleteLocal: () -> Unit,
) {
    when (outcome) {
        is SyncManager.SyncOutcome.Verified -> AlertDialog(
            onDismissRequest = onDismiss,
            title = { Text("Sincronización verificada") },
            text = {
                Text(
                    "Todos los datos, geometrías y fotos fueron confirmados por el " +
                        "servidor. ¿Desea eliminar este trabajo del dispositivo para " +
                        "liberar espacio?"
                )
            },
            confirmButton = {
                TextButton(onClick = onDeleteLocal) { Text("Eliminar del dispositivo") }
            },
            dismissButton = {
                TextButton(onClick = onDismiss) { Text("Conservar") }
            },
        )

        is SyncManager.SyncOutcome.WithIssues -> AlertDialog(
            onDismissRequest = onDismiss,
            title = { Text("Sincronizado con novedades") },
            text = {
                Column {
                    Text(
                        "La información se envió, pero la validación de calidad " +
                            "encontró ${outcome.report.issues.size} novedad(es):",
                        modifier = Modifier.padding(bottom = 8.dp),
                    )
                    LazyColumn(Modifier.heightIn(max = 320.dp)) {
                        items(outcome.report.issues) { issue ->
                            IssueRow(issue)
                            Divider(Modifier.padding(vertical = 6.dp))
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = onDismiss) { Text("Entendido") }
            },
        )

        is SyncManager.SyncOutcome.Pending -> AlertDialog(
            onDismissRequest = onDismiss,
            title = { Text("Sincronización pendiente") },
            text = {
                Text(
                    "${outcome.reason}\n\nEl trabajo queda pendiente y el proceso " +
                        "completo se reintentará; no se perdió ningún dato capturado."
                )
            },
            confirmButton = {
                TextButton(onClick = onDismiss) { Text("Aceptar") }
            },
        )
    }
}

@Composable
private fun IssueRow(issue: QualityIssue) {
    Column(Modifier.fillMaxWidth()) {
        Text(
            "${issue.elementType} · ${issue.elementGuid.take(12)}…",
            fontWeight = FontWeight.SemiBold,
            style = MaterialTheme.typography.bodyLarge,
        )
        Text(issue.message, style = MaterialTheme.typography.bodyLarge)
        val expected = issue.expected
        if (expected != null) {
            Text(
                "Se espera: $expected" + (issue.actual?.let { " · Actual: $it" } ?: ""),
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
        }
    }
}
