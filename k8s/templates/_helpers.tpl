{{/* Common labels applied to every resource in this chart. */}}
{{- define "estimatekit.labels" -}}
app.kubernetes.io/name: estimatekit
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: estimatekit
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end -}}

{{/* Subset suitable for matchLabels / selector. */}}
{{- define "estimatekit.selectorLabels" -}}
app.kubernetes.io/name: estimatekit
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
