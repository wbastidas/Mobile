# Reglas ProGuard/R8 para el build de release.

# kotlinx.serialization: conservar serializadores generados.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**
-keepclassmembers class kotlinx.serialization.json.** { *; }
-keep,includedescriptorclasses class com.empresa.levantamiento.**$$serializer { *; }
-keepclassmembers class com.empresa.levantamiento.** {
    *** Companion;
}
-keepclasseswithmembers class com.empresa.levantamiento.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# Retrofit / OkHttp.
-keepattributes Signature, Exceptions
-dontwarn okhttp3.**
-dontwarn retrofit2.**
