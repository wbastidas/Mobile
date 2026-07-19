package com.empresa.levantamiento.ui.login

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Bolt
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun LoginScreen(onLoggedIn: () -> Unit, vm: LoginViewModel = viewModel()) {
    val state by vm.state
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var deviceUid by remember { mutableStateOf("ANDROID-DEMO-001") }

    // Fondo corporativo con degradado; tarjeta elevada con contraste alto
    // para uso con sol directo (RNF-04).
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.linearGradient(
                    listOf(Color(0xFF101A30), Color(0xFF0B1220), Color(0xFF16213A))
                )
            ),
        contentAlignment = Alignment.Center,
    ) {
        ElevatedCard(modifier = Modifier.widthIn(max = 440.dp).padding(20.dp)) {
            Column(
                modifier = Modifier.padding(28.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                Box(
                    modifier = Modifier
                        .size(56.dp)
                        .background(MaterialTheme.colorScheme.primary, RoundedCornerShape(14.dp)),
                    contentAlignment = Alignment.Center,
                ) {
                    Icon(
                        Icons.Default.Bolt, contentDescription = null,
                        tint = Color.White, modifier = Modifier.size(34.dp),
                    )
                }
                Text(
                    "Levantamiento Eléctrico",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(top = 14.dp),
                )
                Text(
                    "Aplicación de Campo",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(bottom = 10.dp),
                )

                val fieldMod = Modifier.fillMaxWidth().padding(top = 12.dp)
                OutlinedTextField(username, { username = it }, label = { Text("Usuario") },
                    modifier = fieldMod, singleLine = true)
                OutlinedTextField(
                    password, { password = it }, label = { Text("Contraseña") },
                    visualTransformation = PasswordVisualTransformation(),
                    modifier = fieldMod, singleLine = true,
                )
                OutlinedTextField(deviceUid, { deviceUid = it },
                    label = { Text("Dispositivo (UID)") }, modifier = fieldMod, singleLine = true)

                state.error?.let {
                    Text(it, color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.padding(top = 10.dp))
                }

                Button(
                    onClick = { vm.login(username, password, deviceUid, onLoggedIn) },
                    enabled = !state.loading,
                    modifier = Modifier.fillMaxWidth().padding(top = 18.dp).height(50.dp),
                ) {
                    if (state.loading) CircularProgressIndicator(modifier = Modifier.width(22.dp))
                    else Text("Ingresar", style = MaterialTheme.typography.labelLarge)
                }
            }
        }
    }
}
