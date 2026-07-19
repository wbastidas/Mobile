package com.empresa.levantamiento.ui.workdetail

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Sync
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.empresa.levantamiento.sync.SyncManager

/**
 * Detalle de un trabajo con interfaz ADAPTATIVA (RF-MOV-04):
 *  - Teléfono (compacto): transición entre la vista de mapa y la de atributos.
 *  - Tablet (expandido): pantalla dividida con mapa y panel atributivo a la vez.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WorkDetailScreen(
    workId: String,
    isExpandedWidth: Boolean,
    onBack: () -> Unit,
) {
    val vm: WorkDetailViewModel = viewModel(
        factory = viewModelFactory { initializer { WorkDetailViewModel(workId) } }
    )
    val state by vm.state
    var syncOutcome by remember { mutableStateOf<SyncManager.SyncOutcome?>(null) }

    // Resultado de la sincronización: novedades explicadas, oferta de
    // eliminación local tras verificación, o motivo del estado pendiente.
    syncOutcome?.let { outcome ->
        SyncResultDialog(
            outcome = outcome,
            onDismiss = { syncOutcome = null },
            onDeleteLocal = {
                syncOutcome = null
                vm.deleteLocal(onDone = onBack)
            },
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(state.work?.code ?: "Trabajo")
                        Text(
                            "Avance: ${state.completed}/${state.total}",
                            style = MaterialTheme.typography.labelLarge,
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Volver")
                    }
                },
                actions = {
                    IconButton(onClick = { vm.sync { syncOutcome = it } }, enabled = !state.busy) {
                        Icon(Icons.Default.Sync, contentDescription = "Sincronizar trabajo")
                    }
                },
            )
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            if (state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
            state.message?.let {
                Text(it, Modifier.padding(horizontal = 16.dp, vertical = 6.dp))
            }

            if (isExpandedWidth) {
                // Tablet: pantalla dividida (RF-MOV-04.2).
                Row(Modifier.fillMaxSize()) {
                    Box(Modifier.weight(1f).fillMaxSize()) {
                        MapPane(state, onSelect = vm::select)
                    }
                    Divider(
                        Modifier.fillMaxWidth(0.001f), // divisor vertical
                    )
                    Box(Modifier.weight(1f).fillMaxSize()) {
                        AttributePane(vm, state)
                    }
                }
            } else {
                // Teléfono: transición mapa <-> atributos (RF-MOV-04.1).
                var tab by remember { mutableIntStateOf(0) }
                SingleChoiceSegmentedButtonRow(
                    Modifier.fillMaxWidth().padding(horizontal = 12.dp, vertical = 8.dp)
                ) {
                    SegmentedButton(
                        selected = tab == 0,
                        onClick = { tab = 0 },
                        shape = SegmentedButtonDefaults.itemShape(0, 2),
                    ) { Text("Mapa") }
                    SegmentedButton(
                        selected = tab == 1,
                        onClick = { tab = 1 },
                        shape = SegmentedButtonDefaults.itemShape(1, 2),
                    ) { Text("Atributos") }
                }
                Box(Modifier.fillMaxSize()) {
                    if (tab == 0) MapPane(state, onSelect = { vm.select(it); tab = 1 })
                    else AttributePane(vm, state)
                }
            }
        }
    }
}
