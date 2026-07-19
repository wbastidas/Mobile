package com.empresa.levantamiento.core.quality

import com.empresa.levantamiento.core.sync.ValidationIssueDto
import com.empresa.levantamiento.core.sync.ValidationReportDto

/** Convierte el resultado de la validación local en el DTO serializable de sync. */
fun QualityReport.toDto(): ValidationReportDto = ValidationReportDto(
    result = result.name,
    issues = issues.map {
        ValidationIssueDto(
            elementGuid = it.elementGuid,
            elementType = it.elementType,
            field = it.field,
            ruleType = it.ruleType,
            message = it.message,
            expected = it.expected,
            actual = it.actual,
        )
    },
)
