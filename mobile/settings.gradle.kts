pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "LevantamientoElectrico"
include(":app")
include(":core")
// El módulo :core también tiene su propio settings.gradle.kts para poder
// ejecutar sus pruebas JVM sin el SDK de Android (se ignora al incluirlo aquí).
