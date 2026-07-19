package com.empresa.levantamiento

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.Surface
import androidx.compose.material3.windowsizeclass.ExperimentalMaterial3WindowSizeClassApi
import androidx.compose.material3.windowsizeclass.WindowWidthSizeClass
import androidx.compose.material3.windowsizeclass.calculateWindowSizeClass
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.empresa.levantamiento.di.ServiceLocator
import com.empresa.levantamiento.ui.login.LoginScreen
import com.empresa.levantamiento.ui.theme.LevantamientoTheme
import com.empresa.levantamiento.ui.workdetail.WorkDetailScreen
import com.empresa.levantamiento.ui.works.WorksScreen

class MainActivity : ComponentActivity() {

    @OptIn(ExperimentalMaterial3WindowSizeClassApi::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            LevantamientoTheme {
                val windowSizeClass = calculateWindowSizeClass(this)
                // Detección automática del factor de forma (RF-MOV-04.3).
                val isExpanded = windowSizeClass.widthSizeClass == WindowWidthSizeClass.Expanded

                Surface {
                    val navController = rememberNavController()
                    // Punto de partida según la sesión offline persistente (RF-MOV-01.3).
                    var start by remember {
                        mutableStateOf(if (ServiceLocator.session.isLoggedIn) "works" else "login")
                    }

                    NavHost(navController = navController, startDestination = start) {
                        composable("login") {
                            LoginScreen(onLoggedIn = {
                                start = "works"
                                navController.navigate("works") {
                                    popUpTo("login") { inclusive = true }
                                }
                            })
                        }
                        composable("works") {
                            WorksScreen(onOpenWork = { id -> navController.navigate("work/$id") })
                        }
                        composable("work/{workId}") { backStackEntry ->
                            val workId = backStackEntry.arguments?.getString("workId") ?: return@composable
                            WorkDetailScreen(
                                workId = workId,
                                isExpandedWidth = isExpanded,
                                onBack = { navController.popBackStack() },
                            )
                        }
                    }
                }
            }
        }
    }
}
