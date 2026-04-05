/**
 * Decision Engine Screen
 * User asks a life question → AI returns 3-5 scenarios with risk analysis
 */
import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity,
  ScrollView, StyleSheet, ActivityIndicator, Alert,
} from 'react-native';
import { useMutation } from '@tanstack/react-query';
import * as Haptics from 'expo-haptics';

import { decisionsApi } from '../api/client';
import { COLORS, FONTS, SPACING } from '../theme';

const RISK_COLOR = (score: number) => {
  if (score < 30) return '#1D9E75';
  if (score < 60) return '#EF9F27';
  return '#E24B4A';
};

const RECOMMENDATION_LABEL: Record<string, { label: string; color: string }> = {
  yes: { label: 'Go for it', color: '#1D9E75' },
  no: { label: 'Hold back', color: '#E24B4A' },
  conditional: { label: 'Conditional', color: '#EF9F27' },
};

export default function DecisionScreen() {
  const [question, setQuestion] = useState('');
  const [result, setResult] = useState<any>(null);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);

  const simulate = useMutation({
    mutationFn: (q: string) => decisionsApi.simulate(q).then(r => r.data),
    onSuccess: (data) => {
      setResult(data);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    },
    onError: () => Alert.alert('Error', 'Failed to simulate. Check your connection.'),
  });

  const choose = useMutation({
    mutationFn: ({ decisionId, scenarioId }: { decisionId: string; scenarioId: string }) =>
      decisionsApi.choose(decisionId, scenarioId),
    onSuccess: (_, vars) => {
      setSelectedScenario(vars.scenarioId);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    },
  });

  const rec = result?.recommendation ? RECOMMENDATION_LABEL[result.recommendation] : null;

  return (
    <ScrollView style={styles.container} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>Decision Engine</Text>
      <Text style={styles.subtitle}>Ask a real life question. Get scenario analysis.</Text>

      {/* Input */}
      <View style={styles.inputWrapper}>
        <TextInput
          style={styles.input}
          placeholder="Should I quit my job? Move to Berlin? Start a business?"
          placeholderTextColor={COLORS.muted}
          value={question}
          onChangeText={setQuestion}
          multiline
          numberOfLines={3}
          maxLength={300}
        />
        <TouchableOpacity
          style={[styles.simulateBtn, (!question.trim() || simulate.isPending) && styles.disabledBtn]}
          onPress={() => simulate.mutate(question.trim())}
          disabled={!question.trim() || simulate.isPending}
        >
          {simulate.isPending
            ? <ActivityIndicator color="#fff" size="small" />
            : <Text style={styles.simulateBtnText}>Simulate →</Text>
          }
        </TouchableOpacity>
      </View>

      {simulate.isPending && (
        <View style={styles.loadingBox}>
          <Text style={styles.loadingText}>Game Master analyzing your situation…</Text>
          <Text style={styles.loadingSubtext}>Running {result?.scenarios?.length || 4} scenarios</Text>
        </View>
      )}

      {result && (
        <>
          {/* Risk Score */}
          <View style={styles.riskRow}>
            <View style={[styles.riskBadge, { backgroundColor: RISK_COLOR(result.risk_score) + '22' }]}>
              <Text style={[styles.riskScore, { color: RISK_COLOR(result.risk_score) }]}>
                Risk {result.risk_score}/100
              </Text>
            </View>
            {rec && (
              <View style={[styles.recBadge, { backgroundColor: rec.color + '22' }]}>
                <Text style={[styles.recText, { color: rec.color }]}>{rec.label}</Text>
              </View>
            )}
          </View>

          {/* Recommendation */}
          {result.recommendation_rationale && (
            <View style={styles.rationaleBox}>
              <Text style={styles.rationaleLabel}>Game Master's take</Text>
              <Text style={styles.rationaleText}>{result.recommendation_rationale}</Text>
            </View>
          )}

          {/* Scenarios */}
          <Text style={styles.sectionTitle}>Scenarios</Text>
          {result.scenarios?.map((s: any) => (
            <TouchableOpacity
              key={s.id}
              style={[
                styles.scenarioCard,
                selectedScenario === s.id && styles.scenarioSelected,
              ]}
              onPress={() => choose.mutate({ decisionId: result.decision_id, scenarioId: s.id })}
              activeOpacity={0.8}
            >
              <View style={styles.scenarioHeader}>
                <Text style={styles.scenarioLabel}>{s.label}</Text>
                <Text style={styles.probability}>{Math.round((s.probability || 0) * 100)}%</Text>
              </View>
              <Text style={styles.scenarioDesc}>{s.description}</Text>

              <View style={styles.scenarioMeta}>
                <MetaItem label="Financial" value={
                  s.financial_impact_monthly > 0
                    ? `+$${s.financial_impact_monthly?.toLocaleString()}/mo`
                    : `$${s.financial_impact_monthly?.toLocaleString()}/mo`
                } positive={s.financial_impact_monthly > 0} />
                <MetaItem label="Stress" value={`${s.stress_level}/10`} positive={s.stress_level < 6} />
              </View>

              {s.career_impact && (
                <Text style={styles.impactText}>Career: {s.career_impact}</Text>
              )}

              {selectedScenario === s.id && (
                <View style={styles.chosenBadge}>
                  <Text style={styles.chosenText}>✓ Selected</Text>
                </View>
              )}
            </TouchableOpacity>
          ))}

          {/* Risk Factors */}
          {result.risk_factors?.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>Risk Factors</Text>
              {result.risk_factors.map((rf: any, i: number) => (
                <View key={i} style={styles.riskFactor}>
                  <Text style={styles.rfLabel}>{rf.factor}</Text>
                  <Text style={styles.rfMeta}>
                    Weight {Math.round(rf.weight * 100)}% · {rf.mitigable ? 'Mitigable' : 'Hard to avoid'}
                  </Text>
                  {rf.mitigation && <Text style={styles.rfMitigation}>→ {rf.mitigation}</Text>}
                </View>
              ))}
            </>
          )}

          {/* Questions to answer first */}
          {result.questions_to_answer_first?.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>Answer these first</Text>
              {result.questions_to_answer_first.map((q: string, i: number) => (
                <Text key={i} style={styles.dueDiligenceItem}>• {q}</Text>
              ))}
            </>
          )}

          <View style={{ height: 40 }} />
        </>
      )}
    </ScrollView>
  );
}

const MetaItem = ({ label, value, positive }: { label: string; value: string; positive: boolean }) => (
  <View style={styles.metaItem}>
    <Text style={styles.metaLabel}>{label}</Text>
    <Text style={[styles.metaValue, { color: positive ? '#1D9E75' : '#E24B4A' }]}>{value}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.bg, padding: SPACING.md, paddingTop: 60 },
  title: { fontSize: 26, fontWeight: '700', color: COLORS.text, marginBottom: 4 },
  subtitle: { fontSize: 14, color: COLORS.muted, marginBottom: SPACING.lg },
  inputWrapper: { gap: SPACING.sm, marginBottom: SPACING.lg },
  input: {
    backgroundColor: COLORS.surface, borderRadius: 14, padding: SPACING.md,
    color: COLORS.text, fontSize: 15, borderWidth: 1, borderColor: COLORS.border,
    textAlignVertical: 'top', minHeight: 80,
  },
  simulateBtn: {
    backgroundColor: COLORS.accent, borderRadius: 12,
    padding: SPACING.md, alignItems: 'center',
  },
  disabledBtn: { opacity: 0.5 },
  simulateBtnText: { color: '#fff', fontSize: 16, fontWeight: '700' },
  loadingBox: {
    backgroundColor: COLORS.surface, borderRadius: 12, padding: SPACING.lg,
    alignItems: 'center', marginBottom: SPACING.lg, borderWidth: 1, borderColor: COLORS.border,
  },
  loadingText: { color: COLORS.text, fontSize: 14, fontWeight: '500' },
  loadingSubtext: { color: COLORS.muted, fontSize: 12, marginTop: 4 },
  riskRow: { flexDirection: 'row', gap: SPACING.sm, marginBottom: SPACING.md },
  riskBadge: { borderRadius: 20, paddingHorizontal: 14, paddingVertical: 7 },
  riskScore: { fontSize: 14, fontWeight: '700' },
  recBadge: { borderRadius: 20, paddingHorizontal: 14, paddingVertical: 7 },
  recText: { fontSize: 14, fontWeight: '700' },
  rationaleBox: {
    backgroundColor: COLORS.surface, borderRadius: 12, padding: SPACING.md,
    marginBottom: SPACING.lg, borderWidth: 1, borderColor: COLORS.border,
  },
  rationaleLabel: { fontSize: 11, color: COLORS.muted, fontWeight: '600', marginBottom: 6, letterSpacing: 0.5 },
  rationaleText: { color: COLORS.text, fontSize: 14, lineHeight: 21 },
  sectionTitle: { fontSize: 15, fontWeight: '700', color: COLORS.text, marginBottom: SPACING.sm, marginTop: SPACING.lg },
  scenarioCard: {
    backgroundColor: COLORS.surface, borderRadius: 14, padding: SPACING.md,
    marginBottom: SPACING.sm, borderWidth: 1, borderColor: COLORS.border,
  },
  scenarioSelected: { borderColor: COLORS.accent, borderWidth: 1.5 },
  scenarioHeader: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 6 },
  scenarioLabel: { fontSize: 15, fontWeight: '700', color: COLORS.text, flex: 1 },
  probability: { fontSize: 13, color: COLORS.muted, fontWeight: '600' },
  scenarioDesc: { color: COLORS.muted, fontSize: 13, lineHeight: 19, marginBottom: SPACING.sm },
  scenarioMeta: { flexDirection: 'row', gap: SPACING.md, marginBottom: 6 },
  metaItem: { gap: 2 },
  metaLabel: { fontSize: 11, color: COLORS.muted, fontWeight: '600' },
  metaValue: { fontSize: 14, fontWeight: '700' },
  impactText: { fontSize: 12, color: COLORS.muted, marginTop: 4 },
  chosenBadge: {
    position: 'absolute', top: SPACING.md, right: SPACING.md,
    backgroundColor: COLORS.accent + '22', borderRadius: 10, paddingHorizontal: 10, paddingVertical: 4,
  },
  chosenText: { color: COLORS.accent, fontSize: 12, fontWeight: '700' },
  riskFactor: {
    backgroundColor: COLORS.surface, borderRadius: 10, padding: SPACING.md,
    marginBottom: SPACING.sm, borderWidth: 1, borderColor: COLORS.border,
  },
  rfLabel: { color: COLORS.text, fontSize: 14, fontWeight: '600' },
  rfMeta: { color: COLORS.muted, fontSize: 12, marginTop: 3 },
  rfMitigation: { color: '#1D9E75', fontSize: 13, marginTop: 6 },
  dueDiligenceItem: { color: COLORS.muted, fontSize: 14, marginBottom: 6, lineHeight: 20 },
});
