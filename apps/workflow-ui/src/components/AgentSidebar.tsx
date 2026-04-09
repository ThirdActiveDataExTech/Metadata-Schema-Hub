import type { AgentSSEEvent } from '../api/sse'

interface AgentSidebarProps {
  visible: boolean
  onClose: () => void
  onRun: () => void
  title: string
  events: AgentSSEEvent[]
  isRunning: boolean
  error: string | null
  nodeLabels: Record<string, string>
  nodeOrder: string[]
}

/** One-line summary for a completed node */
function formatSummary(node: string, data: Record<string, unknown>): string {
  switch (node) {
    case 'parse_context': {
      const fields = data.low_confidence_fields
      return Array.isArray(fields) ? `Low confidence: ${fields.length}개 필드` : ''
    }
    case 'enrich_metadata_candidates':
      return data.schema_match_dto_count != null ? `DTO 후보 ${data.schema_match_dto_count}개 탐색` : ''
    case 'decide_field_mappings':
      return `${data.decisions_count ?? 0}개 결정, ${data.errors_count ?? 0}개 오류`
    case 'validate_decisions':
      return data.validated_update_count != null ? `${data.validated_update_count}개 검증 완료` : ''
    case 'build_draft_response':
      return `${data.update_count ?? 0}개 필드 업데이트`
    case 'assess_mapping_quality': {
      const score = typeof data.mapping_score === 'number' ? (data.mapping_score * 100).toFixed(1) : '?'
      return `Score: ${score}%, Tier: ${data.quality_tier ?? '?'}`
    }
    case 'assess_entity_overlap':
      return `${data.scenario ?? '?'}, 후보 ${data.candidate_count ?? 0}개`
    case 'reason_merge_decision':
      return `결정: ${data.decision ?? '?'}`
    case 'build_merge_response':
      return `${data.decision ?? '?'}`
    default:
      return ''
  }
}

/** Data sample lines for a completed node */
function formatDetail(node: string, data: Record<string, unknown>): string[] {
  switch (node) {
    case 'parse_context': {
      const fields = data.low_confidence_fields
      if (Array.isArray(fields) && fields.length > 0) {
        const shown = fields.slice(0, 5).join(', ')
        return fields.length > 5 ? [`${shown} ...+${fields.length - 5}`] : [shown]
      }
      return []
    }
    case 'enrich_metadata_candidates':
      return data.schema_match_dto_count != null ? [`schema_match_dto_count: ${data.schema_match_dto_count}`] : []
    case 'decide_field_mappings': {
      const lines: string[] = []
      if (data.decisions_count != null) lines.push(`decisions: ${data.decisions_count}`)
      if (data.errors_count != null && Number(data.errors_count) > 0) lines.push(`errors: ${data.errors_count}`)
      return lines
    }
    case 'validate_decisions':
      return data.validated_update_count != null ? [`validated: ${data.validated_update_count}`] : []
    case 'build_draft_response':
      return [`draft_id: ${data.draft_id ?? '?'}, updates: ${data.update_count ?? 0}`]
    case 'assess_mapping_quality': {
      const lines: string[] = []
      if (typeof data.mapping_score === 'number') lines.push(`score: ${(data.mapping_score * 100).toFixed(1)}%`)
      if (data.quality_tier) lines.push(`tier: ${data.quality_tier}`)
      const lcf = data.low_confidence_fields
      if (Array.isArray(lcf) && lcf.length > 0) lines.push(`low_conf: ${lcf.slice(0, 3).join(', ')}`)
      return lines
    }
    case 'assess_entity_overlap': {
      const lines: string[] = []
      if (data.scenario) lines.push(`scenario: ${data.scenario}`)
      if (data.candidate_count != null) lines.push(`candidates: ${data.candidate_count}`)
      if (data.best_candidate_entry_id != null) lines.push(`best: #${data.best_candidate_entry_id}`)
      return lines
    }
    case 'reason_merge_decision': {
      const lines: string[] = []
      if (data.decision) lines.push(`decision: ${data.decision}`)
      if (data.has_error) lines.push(`has_error: true`)
      return lines
    }
    case 'build_merge_response':
      return [`merge_id: ${data.merge_id ?? '?'}, decision: ${data.decision ?? '?'}`]
    default:
      return []
  }
}

export default function AgentSidebar({
  visible,
  onClose,
  onRun,
  title,
  events,
  isRunning,
  error,
  nodeLabels,
  nodeOrder,
}: AgentSidebarProps) {
  const completedNodes = new Set(
    events.filter((e) => e.type === 'node_complete').map((e) => e.node),
  )
  const resultEvent = events.find((e) => e.type === 'final_response')
  const currentNodeIndex = nodeOrder.findIndex((n) => !completedNodes.has(n))
  const hasEvents = events.length > 0

  return (
    <div className={`agent-sidebar ${visible ? 'visible' : ''}`}>
      <div className="agent-sidebar-header">
        <span className="agent-sidebar-title">AI 에이전트 — {title}</span>
        <button className="agent-sidebar-close" onClick={onClose} aria-label="Close">
          &times;
        </button>
      </div>

      <div className="agent-sidebar-body">
        {/* Run button */}
        <button
          className="agent-sidebar-run-btn"
          onClick={onRun}
          disabled={isRunning}
        >
          {isRunning ? '처리 중...' : hasEvents ? '다시 실행' : '에이전트 실행'}
        </button>

        {/* Status */}
        {error && <div className="agent-status-banner error">{error}</div>}
        {!error && !isRunning && resultEvent && (
          <div className="agent-status-banner success">처리 완료</div>
        )}

        {/* Timeline */}
        {hasEvents && (
          <div className="agent-timeline">
            {nodeOrder.map((nodeName, idx) => {
              const isCompleted = completedNodes.has(nodeName)
              const isActive = isRunning && idx === currentNodeIndex
              const nodeEvent = events.find(
                (e) => e.type === 'node_complete' && e.node === nodeName,
              )
              const summary = nodeEvent ? formatSummary(nodeName, nodeEvent.data) : ''
              const detail = nodeEvent ? formatDetail(nodeName, nodeEvent.data) : []

              return (
                <div
                  key={nodeName}
                  className={`agent-step ${isCompleted ? 'completed' : ''} ${isActive ? 'in-progress' : ''}`}
                >
                  <div className="agent-step-track">
                    <div
                      className={`agent-step-icon ${isCompleted ? 'completed' : ''} ${isActive ? 'in-progress' : ''}`}
                    >
                      {isCompleted ? '✓' : isActive ? '⟳' : '·'}
                    </div>
                    {idx < nodeOrder.length - 1 && (
                      <div className={`agent-step-connector ${isCompleted ? 'completed' : ''}`} />
                    )}
                  </div>
                  <div className="agent-step-content">
                    <div className="agent-step-label">
                      {nodeLabels[nodeName] || nodeName}
                      {nodeEvent?.timestamp && (
                        <span className="agent-step-time">
                          {new Date(nodeEvent.timestamp).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                    {summary && <div className="agent-step-summary">{summary}</div>}
                    {detail.length > 0 && (
                      <div className="agent-step-detail">
                        {detail.map((line, i) => (
                          <div key={i}>{line}</div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Result card */}
        {resultEvent && (
          <div className="agent-sidebar-result">
            <div className="agent-sidebar-result-title">에이전트 응답 완료</div>
            {typeof resultEvent.data.decision === 'string' && (
              <div className="agent-sidebar-result-decision">
                <span className={`decision-tag decision-${String(resultEvent.data.decision)}`}>
                  {String(resultEvent.data.decision).toUpperCase()}
                </span>
              </div>
            )}
            {typeof resultEvent.data.reason === 'string' && (
              <div className="agent-sidebar-result-reason">
                {String(resultEvent.data.reason)}
              </div>
            )}
            {Array.isArray(resultEvent.data.updates) && (
              <div className="agent-sidebar-result-reason">
                {resultEvent.data.updates.length}개 필드 업데이트
              </div>
            )}
          </div>
        )}

        {/* Empty state */}
        {!hasEvents && !isRunning && !error && (
          <div className="agent-sidebar-empty">
            실행 버튼을 눌러 에이전트 분석을 시작하세요.
          </div>
        )}
      </div>
    </div>
  )
}
