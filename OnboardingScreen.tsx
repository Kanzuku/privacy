/**
 * Multi-step onboarding — collects the full user profile
 */
import React, { useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity, StyleSheet, ActivityIndicator } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useProfileStore } from '../store';
import { Colors, Typography, Spacing, Radii } from '../theme';

const STEPS = [
  { title: 'The Basics', fields: ['age', 'location', 'job', 'industry'] },
  { title: 'Finances', fields: ['income', 'savings'] },
  { title: 'Life Scores', fields: ['health', 'energy', 'happiness', 'discipline'] },
  { title: 'Habits (1–10)', fields: ['habit_sleep', 'habit_sport', 'habit_learning'] },
  { title: 'Personality', fields: ['risk_tolerance'] },
];

const PLACEHOLDERS: Record<string, string> = {
  age:'28', location:'New York, USA', job:'Software Engineer', industry:'Tech',
  income:'5000 (monthly USD)', savings:'15000', health:'65', energy:'55',
  happiness:'60', discipline:'50', habit_sleep:'6', habit_sport:'3',
  habit_learning:'5', risk_tolerance:'6',
};

export default function OnboardingScreen({ navigation }: any) {
  const insets = useSafeAreaInsets();
  const { updateProfile } = useProfileStore();
  const [step, setStep] = useState(0);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const currentStep = STEPS[step];
  const progress = (step + 1) / STEPS.length;

  const setField = (field: string, value: string) => setValues(v => ({ ...v, [field]: value }));

  const next = async () => {
    if (step < STEPS.length - 1) { setStep(s => s + 1); return; }
    setLoading(true);
    try {
      const parsed: Record<string, any> = {};
      for (const [k, v] of Object.entries(values)) {
        parsed[k] = isNaN(Number(v)) ? v : Number(v);
      }
      await updateProfile(parsed);
      navigation.reset({ index: 0, routes: [{ name: 'Main' }] });
    } catch(e: any) { console.error(e); }
    finally { setLoading(false); }
  };

  return (
    <ScrollView style={{ flex:1, backgroundColor: Colors.bg.primary }} contentContainerStyle={{ paddingTop: insets.top + Spacing.xl, paddingHorizontal: Spacing.xl }} keyboardShouldPersistTaps="handled">
      {/* Progress */}
      <View style={{ height: 3, backgroundColor: Colors.border.subtle, borderRadius: 2, marginBottom: Spacing.xl, overflow:'hidden' }}>
        <View style={{ width:`${progress * 100}%`, height:'100%', backgroundColor: Colors.brand.purple, borderRadius: 2 }} />
      </View>
      <Text style={{ fontSize: Typography.sizes.xs, color: Colors.text.muted, textTransform:'uppercase', letterSpacing:1, marginBottom: Spacing.sm }}>Step {step + 1} of {STEPS.length}</Text>
      <Text style={{ fontSize: Typography.sizes['2xl'], fontWeight:'700', color: Colors.text.primary, marginBottom: Spacing.xl }}>{currentStep.title}</Text>
      {currentStep.fields.map(field => (
        <View key={field} style={{ marginBottom: Spacing.lg }}>
          <Text style={{ fontSize: Typography.sizes.sm, color: Colors.text.secondary, marginBottom: Spacing.xs, textTransform:'capitalize' }}>{field.replace('_', ' ')}</Text>
          <TextInput
            style={{ backgroundColor: Colors.bg.secondary, borderRadius: Radii.md, padding: Spacing.lg, color: Colors.text.primary, fontSize: Typography.sizes.base, borderWidth: 0.5, borderColor: Colors.border.default }}
            placeholder={PLACEHOLDERS[field] ?? ''}
            placeholderTextColor={Colors.text.muted}
            value={values[field] ?? ''}
            onChangeText={v => setField(field, v)}
            keyboardType={['age','income','savings','health','energy','happiness','discipline','habit_sleep','habit_sport','habit_learning','risk_tolerance'].includes(field) ? 'numeric' : 'default'}
          />
        </View>
      ))}
      <TouchableOpacity onPress={next} disabled={loading} style={{ backgroundColor: Colors.brand.purple, borderRadius: Radii.md, padding: Spacing.lg, alignItems:'center', marginTop: Spacing.lg, marginBottom: Spacing['3xl'] }}>
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={{ color:'#fff', fontWeight:'700', fontSize: Typography.sizes.base }}>{step < STEPS.length - 1 ? 'Continue →' : 'Start My Journey'}</Text>}
      </TouchableOpacity>
    </ScrollView>
  );
}
