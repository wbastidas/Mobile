package com.empresa.levantamiento.ui.login

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
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
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel

@Composable
fun LoginScreen(onLoggedIn: () -> Unit, vm: LoginViewModel = viewModel()) {
    val state by vm.state
    var username by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var deviceUid by remember { mutableStateOf("ANDROID-DEMO-001") }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text("Levantamiento Eléctrico", style = MaterialTheme.typography.titleLarge)
        Text("App de Campo", style = MaterialTheme.typography.bodyLarge)

        val fieldMod = Modifier.widthIn(max = 420.dp).width(420.dp).padding(top = 12.dp)
        OutlinedTextField(username, { username = it }, label = { Text("Usuario") }, modifier = fieldMod, singleLine = true)
        OutlinedTextField(
            password, { password = it }, label = { Text("Contraseña") },
            visualTransformation = PasswordVisualTransformation(), modifier = fieldMod, singleLine = true,
        )
        OutlinedTextField(deviceUid, { deviceUid = it }, label = { Text("Dispositivo (UID)") }, modifier = fieldMod, singleLine = true)

        state.error?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(top = 8.dp)) }

        Button(
            onClick = { vm.login(username, password, deviceUid, onLoggedIn) },
            enabled = !state.loading,
            modifier = Modifier.padding(top = 16.dp),
        ) {
            if (state.loading) CircularProgressIndicator(modifier = Modifier.width(20.dp))
            else Text("Ingresar")
        }
    }
}
