/**
 * ME — The Life Game | Shared UI Components
 * StatBar, QuestCard, LevelRing, StreakBadge
 */
import React from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  Animated, ViewStyle,
} from 'react-native';
import { Colors, Typography, Spacing, Radii } from '../theme';
import type { Quest } from '../services/api';

// ─── StatBar ──────────────────────────────────────────────────────────────────

interface StatBarProps {
  label: string;
  value: number;   // 0–100
  color: string;
  style?: ViewStyle;
}

export function StatBar({ label, value, color, style }: StatBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const tier = clamped >= 75 ? 'high' : clamped >= 40 ? 'mid' : 'low';
  const tierColor = tier === 'high' ? color : tier === 'mid' ? Colors.warning : Colors.danger;

  return (
    <View style={[statStyles.container, style]}>
      <View style={statStyles.labelRow}>
        <Text style={statStyles.label}>{label}</Text>
        <Text style={[statStyles.value, { color: tierColor }]}>{clamped}</Text>
      </View>
      <View style={statStyles.track}>
        <View style={[statStyles.fill, { width: `${clamped}%`, backgroundColor: tierColor }]} />
      </View>
    </View>
  );
}

const statStyles = StyleSheet.create({
  container: { backgroundColor: Colors.bg.secondary, borderRadius: Radii.md, padding: Spacing.md, borderWidth: 0.5, borderColor: Colors.border.subtle },
  labelRow:  { flexDirection: 'row', justifyContent: 'space-between', marginBottom: Spacing.xs },
  label:     { fontSize: Typography.sizes.sm, color: Colors.text.secondary },
  value:     { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold },
  track:     { height: 4, backgroundColor: Colors.border.subtle, borderRadius: Radii.full, overflow: 'hidden' },
  fill:      { height: '100%', borderRadius: Radii.full },
});

// ─── QuestCard ────────────────────────────────────────────────────────────────

interface QuestCardProps {
  quest: Quest;
  onComplete: () => void;
  onFail: () => void;
}

const QUEST_TYPE_COLORS: Record<string, string> = {
  daily:   Colors.brand.teal,
  weekly:  Colors.brand.amber,
  main:    Colors.brand.purple,
  skill:   Colors.info,
};

export function QuestCard({ quest, onComplete, onFail }: QuestCardProps) {
  const typeColor = QUEST_TYPE_COLORS[quest.type] ?? Colors.brand.purple;
  const difficultyDots = Array.from({ length: 10 }, (_, i) => i < (quest.difficulty ?? 5));

  return (
    <View style={questStyles.card}>
      <View style={questStyles.header}>
        <View style={[questStyles.typeBadge, { backgroundColor: typeColor + '22', borderColor: typeColor }]}>
          <Text style={[questStyles.typeText, { color: typeColor }]}>{quest.type.toUpperCase()}</Text>
        </View>
        <Text style={questStyles.xp}>+{quest.xp_reward} XP</Text>
      </View>

      <Text style={questStyles.title}>{quest.title}</Text>
      <Text style={questStyles.description} numberOfLines={3}>{quest.description}</Text>

      {/* Stat rewards preview */}
      {quest.stat_rewards && Object.entries(quest.stat_rewards).length > 0 && (
        <View style={questStyles.rewards}>
          {Object.entries(quest.stat_rewards).map(([stat, delta]) => (
            <View key={stat} style={questStyles.rewardChip}>
              <Text style={questStyles.rewardText}>
                {(delta as number) > 0 ? '+' : ''}{delta as number} {stat}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* Difficulty */}
      <View style={questStyles.diffRow}>
        <Text style={questStyles.diffLabel}>Difficulty</Text>
        <View style={questStyles.dots}>
          {difficultyDots.map((active, i) => (
            <View key={i} style={[questStyles.dot, active && questStyles.dotActive]} />
          ))}
        </View>
      </View>

      {/* Action steps */}
      {quest.action_steps && quest.action_steps.length > 0 && (
        <View style={questStyles.steps}>
          {quest.action_steps.slice(0, 3).map((step, i) => (
            <Text key={i} style={questStyles.step}>• {step.action}</Text>
          ))}
        </View>
      )}

      {/* Due date */}
      {quest.due_at && (
        <Text style={questStyles.due}>Due: {new Date(quest.due_at).toLocaleDateString()}</Text>
      )}

      {/* Buttons */}
      <View style={questStyles.buttons}>
        <TouchableOpacity style={questStyles.failBtn} onPress={onFail}>
          <Text style={questStyles.failBtnText}>Fail</Text>
        </TouchableOpacity>
        <TouchableOpacity style={questStyles.completeBtn} onPress={onComplete}>
          <Text style={questStyles.completeBtnText}>Complete ✓</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const questStyles = StyleSheet.create({
  card:        { backgroundColor: Colors.bg.secondary, borderRadius: Radii.lg, padding: Spacing.lg, marginBottom: Spacing.md, borderWidth: 0.5, borderColor: Colors.border.subtle },
  header:      { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.sm },
  typeBadge:   { borderWidth: 1, borderRadius: Radii.sm, paddingHorizontal: Spacing.sm, paddingVertical: 2 },
  typeText:    { fontSize: Typography.sizes.xs, fontWeight: Typography.weights.bold, letterSpacing: 1 },
  xp:          { fontSize: Typography.sizes.sm, color: Colors.brand.amber, fontWeight: Typography.weights.semibold },
  title:       { fontSize: Typography.sizes.lg, fontWeight: Typography.weights.semibold, color: Colors.text.primary, marginBottom: Spacing.xs },
  description: { fontSize: Typography.sizes.sm, color: Colors.text.secondary, lineHeight: 20, marginBottom: Spacing.md },
  rewards:     { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.xs, marginBottom: Spacing.sm },
  rewardChip:  { backgroundColor: Colors.bg.tertiary, borderRadius: Radii.sm, paddingHorizontal: Spacing.sm, paddingVertical: 2 },
  rewardText:  { fontSize: Typography.sizes.xs, color: Colors.brand.teal },
  diffRow:     { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm, marginBottom: Spacing.sm },
  diffLabel:   { fontSize: Typography.sizes.xs, color: Colors.text.muted },
  dots:        { flexDirection: 'row', gap: 3 },
  dot:         { width: 6, height: 6, borderRadius: 3, backgroundColor: Colors.border.default },
  dotActive:   { backgroundColor: Colors.brand.amber },
  steps:       { marginBottom: Spacing.sm },
  step:        { fontSize: Typography.sizes.sm, color: Colors.text.secondary, marginBottom: 2 },
  due:         { fontSize: Typography.sizes.xs, color: Colors.text.muted, marginBottom: Spacing.md },
  buttons:     { flexDirection: 'row', gap: Spacing.sm },
  failBtn:     { flex: 1, paddingVertical: Spacing.sm, borderRadius: Radii.md, alignItems: 'center', borderWidth: 0.5, borderColor: Colors.danger },
  failBtnText: { fontSize: Typography.sizes.sm, color: Colors.danger },
  completeBtn: { flex: 2, paddingVertical: Spacing.sm, borderRadius: Radii.md, alignItems: 'center', backgroundColor: Colors.brand.teal },
  completeBtnText: { fontSize: Typography.sizes.sm, fontWeight: Typography.weights.semibold, color: '#fff' },
});

// ─── LevelRing ────────────────────────────────────────────────────────────────

export function LevelRing({ level, progress }: { level: number; progress: number }) {
  const size = 80;
  const stroke = 6;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - progress);

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <View style={{ position: 'absolute' }}>
        {/* SVG-equivalent using border trick */}
        <View style={{
          width: size, height: size, borderRadius: size / 2,
          borderWidth: stroke, borderColor: Colors.border.subtle,
        }} />
      </View>
      <View style={{
        position: 'absolute',
        width: size - stroke * 2, height: size - stroke * 2,
        borderRadius: (size - stroke * 2) / 2,
        borderWidth: stroke,
        borderColor: Colors.brand.purple,
        borderTopColor: Colors.border.subtle,
        transform: [{ rotate: `${progress * 360 - 90}deg` }],
      }} />
      <Text style={{ fontSize: Typography.sizes['2xl'], fontWeight: Typography.weights.bold, color: Colors.text.primary }}>
        {level}
      </Text>
    </View>
  );
}

// ─── StreakBadge ──────────────────────────────────────────────────────────────

export function StreakBadge({ streak = 0 }: { streak?: number }) {
  return (
    <View style={streakStyles.badge}>
      <Text style={streakStyles.fire}>🔥</Text>
      <Text style={streakStyles.count}>{streak}</Text>
    </View>
  );
}

const streakStyles = StyleSheet.create({
  badge: { flexDirection: 'row', alignItems: 'center', backgroundColor: Colors.brand.coral + '22', borderRadius: Radii.full, paddingHorizontal: Spacing.md, paddingVertical: Spacing.xs, borderWidth: 1, borderColor: Colors.brand.coral + '44' },
  fire:  { fontSize: 16, marginRight: 4 },
  count: { fontSize: Typography.sizes.base, fontWeight: Typography.weights.bold, color: Colors.brand.coral },
});
