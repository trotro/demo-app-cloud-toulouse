{{- define "clean-release-name"}}
  {{- $name := .Release.Name }}
  {{- $formattedName := lower $name | replace " " "-" | replace "_" "-" }}
  {{- trim $formattedName }}
{{- end}}