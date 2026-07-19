package com.empresa.levantamiento.ui.works

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.empresa.levantamiento.ui.components.StatusChip
import com.empresa.levantamiento.ui.components.workTypeLabel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WorksScreen(onOpenWork: (String) -> Unit, vm: WorksViewModel = viewModel()) {
    val state by vm.state

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Mis trabajos") },
                actions = {
                    IconButton(onClick = { vm.pull() }, enabled = !state.syncing) {
                        Icon(Icons.Default.Refresh, contentDescription = "Sincronizar")
                    }
                },
            )
        },
    ) { padding ->
        Column(Modifier.fillMaxSize().padding(padding)) {
            if (state.syncing) LinearProgressIndicator(Modifier.fillMaxWidth())
            state.message?.let {
                Text(it, Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                    style = MaterialTheme.typography.bodyLarge)
            }
            if (state.works.isEmpty()) {
                Text(
                    "No hay trabajos descargados. Pulse sincronizar cuando tenga conexión.",
                    Modifier.padding(24.dp),
                )
            } else {
                LazyColumn(
                    Modifier.fillMaxSize().padding(12.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    items(state.works, key = { it.id }) { w ->
                        Card(
                            onClick = { onOpenWork(w.id) },
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Column(Modifier.padding(16.dp)) {
                                Row(
                                    Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                ) {
                                    Text(w.code, fontWeight = FontWeight.Bold)
                                    StatusChip(w.status)
                                }
                                Text(w.title, style = MaterialTheme.typography.bodyLarge)
                                Text(
                                    workTypeLabel(w.type),
                                    style = MaterialTheme.typography.labelLarge,
                                    color = MaterialTheme.colorScheme.primary,
                                )
                                // Avance porcentual del trabajo (RF-MOV-05).
                                val (done, total) = state.progress[w.id] ?: (0 to 0)
                                if (total > 0) {
                                    LinearProgressIndicator(
                                        progress = { done.toFloat() / total },
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .padding(top = 10.dp),
                                    )
                                    Text(
                                        "$done de $total elementos completados",
                                        style = MaterialTheme.typography.labelLarge,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        modifier = Modifier.padding(top = 4.dp),
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
