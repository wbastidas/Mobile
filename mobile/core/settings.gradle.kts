// Settings STANDALONE del módulo core (Kotlin puro, sin Android).
// Permite compilar y ejecutar sus pruebas de forma independiente del SDK Android:
//   cd mobile/core && gradle test
// Cuando se incluye desde el build raíz (../settings.gradle.kts) este archivo se ignora.
rootProject.name = "core"

dependencyResolutionManagement {
    repositories {
        mavenCentral()
        google()
    }
}
