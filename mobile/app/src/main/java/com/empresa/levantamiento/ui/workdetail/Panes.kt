package com.empresa.levantamiento.ui.workdetail

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.empresa.levantamiento.core.model.ElementRecord

/**
 * Vista de "mapa" con la presentación según el tipo de trabajo (RF-MOV-05).
 * En esta iteración el lienzo del mapa es un marcador de posición; la capa
 * geográfica interactiva (MapLibre/osmdroid) se integra sobre esta misma
 * estructura. Los elementos se listan y son seleccionables.
 */
@Composable
fun MapPane(state: WorkDetailState, onSelect: (String) -> Unit) {
    Column(Modifier.fillMaxSize()) {
        // Lienzo del mapa (placeholder). El sector/GeoJSON está disponible en el trabajo.
        Box(
            Modifier
                .fillMaxWidth()
                .padding(12.dp)
                .background(Color(0xFFE2E8F0), RoundedCornerShape(12.dp))
                .padding(24.dp),
            contentAlignment = Alignment.Center,
        ) {
            val hint = when (state.work?.type) {
                "REVISION_RED" -> "Mapa del sector · ${state.total} elementos"
                "ORDEN_PUNTUAL" -> "Navegación asistida a elementos objetivo"
                "MANTENIMIENTO" -> "Captura de elementos nuevos y modificados"
                else -> "Mapa"
            }
            Text(hint, color = Color(0xFF475569), fontWeight = FontWeight.SemiBold)
        }

        Text(
            "Elementos del trabajo",
            Modifier.padding(horizontal = 16.dp),
            style = MaterialTheme.typography.titleLarge,
        )
        LazyColumn(
            Modifier.fillMaxSize().padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            items(state.elements, key = { it.guid }) { e ->
                Card(onClickCompat = { onSelect(e.guid) }, modifier = Modifier.fillMaxWidth()) {
                    Row(
                        Modifier.fillMaxWidth().padding(14.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Column {
                            Text(e.elementType, fontWeight = FontWeight.Bold)
                            Text(
                                e.guid.take(18) + "…",
                                style = MaterialTheme.typography.labelLarge,
                                color = MaterialTheme.colorScheme.primary,
                            )
                        }
                        Text(if (e.photoCount > 0) "${e.photoCount} 📷" else "sin fotos")
                    }
                }
            }
        }
    }
}

/** Panel atributivo: captura y edición del elemento seleccionado (RF-MOV-06/07). */
@Composable
fun AttributePane(vm: WorkDetailViewModel, state: WorkDetailState) {
    val selected = state.elements.firstOrNull { it.guid == state.selectedGuid }
    if (selected == null) {
        Column(Modifier.fillMaxSize().padding(24.dp)) {
            Text("Seleccione un elemento en el mapa para editar sus atributos,")
            Text("o cree uno nuevo si el trabajo lo permite.")
            if (state.work?.type == "MANTENIMIENTO") {
                Button(
                    onClick = { vm.newElement("POSTE", parentGuid = null) },
                    modifier = Modifier.padding(top = 16.dp),
                ) { Text("+ Nuevo elemento (POSTE)") }
            }
        }
        return
    }
    CaptureForm(vm, selected)
}

@Composable
private fun CaptureForm(vm: WorkDetailViewModel, element: ElementRecord) {
    // Editor dinámico de atributos (en producción se genera desde el esquema, §6.4).
    var attributes by remember(element.guid) {
        mutableStateOf(element.attributes.ifEmpty { mapOf("material" to "", "altura_m" to "") })
    }
    var observations by remember(element.guid) { mutableStateOf("") }
    var newKey by remember(element.guid) { mutableStateOf("") }

    Column(
        Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(element.elementType, style = MaterialTheme.typography.titleLarge)
        Text("GUID: ${element.guid}", style = MaterialTheme.typography.labelLarge)
        element.parentGuid?.let { Text("Padre (puesto/unidad): $it") }

        attributes.forEach { (key, value) ->
            OutlinedTextField(
                value = value ?: "",
                onValueChange = { attributes = attributes.toMutableMap().apply { put(key, it) } },
                label = { Text(key) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
        }

        // Agregar un campo atributivo adicional.
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(
                value = newKey, onValueChange = { newKey = it },
                label = { Text("Nuevo campo") }, modifier = Modifier.weight(1f), singleLine = true,
            )
            OutlinedButton(
                onClick = {
                    if (newKey.isNotBlank()) {
                        attributes = attributes + (newKey to "")
                        newKey = ""
                    }
                },
                modifier = Modifier.padding(start = 8.dp),
            ) { Text("+") }
        }

        OutlinedTextField(
            value = observations, onValueChange = { observations = it },
            label = { Text("Observaciones") }, modifier = Modifier.fillMaxWidth(),
        )

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            // Modo "solo punto + fotos" (RF-MOV-07): sella la posición actual.
            FilledTonalButton(onClick = { vm.capturePoint(element) }) { Text("Capturar punto") }
            FilledTonalButton(
                onClick = { vm.addPhoto(element.guid, ByteArray(0)) },
            ) { Text("Agregar foto") }
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedButton(
                onClick = { vm.saveElement(element, attributes, observations, completed = false) },
            ) { Text("Guardar") }
            Button(
                onClick = { vm.saveElement(element, attributes, observations, completed = true) },
            ) { Text("Guardar y completar") }
        }
    }
}

/** Envoltura para usar Card clickeable sin propagar la anotación experimental. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun Card(onClickCompat: () -> Unit, modifier: Modifier, content: @Composable () -> Unit) {
    androidx.compose.material3.Card(onClick = onClickCompat, modifier = modifier) { content() }
}
