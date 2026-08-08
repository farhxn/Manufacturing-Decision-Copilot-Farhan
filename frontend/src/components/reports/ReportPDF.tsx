'use client';

/**
 * ReportPDF — @react-pdf/renderer document template.
 *
 * Renders a professional executive procurement report as a PDF.
 * Uses dynamic import on the call site so the heavy renderer bundle
 * is never included in the initial page load.
 */

import React from 'react';
import {
  Document,
  Page,
  Text,
  View,
  StyleSheet,
  Font,
} from '@react-pdf/renderer';

// ── Types ─────────────────────────────────────────────────────────────────────

export interface RankedSupplierRow {
  rank: number;
  supplier_name: string;
  country: string;
  final_score: number;
  landed_cost: number;
  lead_time_days: number;
}

export interface ReportPDFData {
  project_name: string;
  generated_at: string;
  recommended_supplier_name: string;
  confidence_score: number;
  confidence_label: string;
  confidence_explanation: string;
  executive_summary: string;
  recommendation_statement: string;
  key_findings: string[];
  risk_summary: string[];
  next_steps: string[];
  disclaimer: string;
  ranking: RankedSupplierRow[];
  evidence_count: number;
  ai_narrative: boolean;
}

// ── Design tokens (PDF uses pt units) ────────────────────────────────────────

const BRAND    = '#7C3AED';   // purple AI accent
const INK      = '#0F172A';   // midnight
const SURFACE  = '#F8FAFC';   // background
const BORDER   = '#E2E8F0';
const SUCCESS  = '#16A34A';
const WARNING  = '#D97706';
const MUTED    = '#64748B';
const WHITE    = '#FFFFFF';

// ── Styles ────────────────────────────────────────────────────────────────────

const s = StyleSheet.create({
  page: {
    fontFamily: 'Helvetica',
    fontSize: 9,
    color: INK,
    backgroundColor: WHITE,
    paddingTop: 48,
    paddingBottom: 48,
    paddingHorizontal: 48,
  },

  // Header strip
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottomWidth: 2,
    borderBottomColor: BRAND,
    paddingBottom: 12,
    marginBottom: 20,
  },
  headerLeft: { flexDirection: 'column', gap: 2 },
  headerTitle: { fontSize: 18, fontFamily: 'Helvetica-Bold', color: INK, letterSpacing: 0.3 },
  headerSubtitle: { fontSize: 9, color: MUTED, marginTop: 2 },
  headerMeta: { fontSize: 8, color: MUTED, textAlign: 'right' },

  // Section headings
  sectionTitle: {
    fontSize: 8,
    fontFamily: 'Helvetica-Bold',
    color: MUTED,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: 18,
    marginBottom: 6,
    borderBottomWidth: 0.5,
    borderBottomColor: BORDER,
    paddingBottom: 3,
  },

  // Recommendation hero card
  heroCard: {
    backgroundColor: SURFACE,
    borderLeftWidth: 4,
    borderLeftColor: BRAND,
    borderRadius: 4,
    padding: 12,
    marginBottom: 4,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  heroSupplierName: { fontSize: 15, fontFamily: 'Helvetica-Bold', color: INK, marginBottom: 3 },
  heroBadge: {
    fontSize: 7,
    fontFamily: 'Helvetica-Bold',
    color: BRAND,
    backgroundColor: '#EDE9FE',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
    marginBottom: 4,
  },
  heroScoreBox: { alignItems: 'flex-end' },
  heroScoreLabel: { fontSize: 7, color: MUTED, textTransform: 'uppercase', letterSpacing: 0.5 },
  heroScore: { fontSize: 28, fontFamily: 'Helvetica-Bold', color: BRAND },
  heroScoreSub: { fontSize: 7, color: MUTED },

  // Confidence bar
  confRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 6 },
  confBarBg: { flex: 1, height: 5, backgroundColor: BORDER, borderRadius: 3 },
  confBarFill: { height: 5, borderRadius: 3, backgroundColor: BRAND },
  confLabel: { fontSize: 8, color: MUTED, width: 60, textAlign: 'right' },

  // Summary paragraph
  summaryBox: {
    backgroundColor: SURFACE,
    borderRadius: 4,
    padding: 10,
    marginTop: 6,
  },
  summaryText: { fontSize: 9, color: INK, lineHeight: 1.6 },

  // AI badge
  aiBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EDE9FE',
    borderRadius: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    marginTop: 6,
    alignSelf: 'flex-start',
  },
  aiBadgeText: { fontSize: 8, color: BRAND, fontFamily: 'Helvetica-Bold' },

  // Bullet lists
  bulletRow: { flexDirection: 'row', marginBottom: 3, gap: 5 },
  bullet: { fontSize: 9, color: BRAND, width: 10 },
  bulletText: { fontSize: 9, color: INK, flex: 1, lineHeight: 1.5 },
  bulletTextWarning: { fontSize: 9, color: WARNING, flex: 1, lineHeight: 1.5 },

  // Two-column grid
  twoCol: { flexDirection: 'row', gap: 16, marginTop: 4 },
  col: { flex: 1 },
  colTitle: { fontSize: 8, fontFamily: 'Helvetica-Bold', color: MUTED, marginBottom: 4, textTransform: 'uppercase', letterSpacing: 0.8 },

  // Ranking table
  table: { marginTop: 6 },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: SURFACE,
    borderBottomWidth: 1,
    borderBottomColor: BORDER,
    paddingVertical: 5,
    paddingHorizontal: 6,
  },
  tableRow: {
    flexDirection: 'row',
    borderBottomWidth: 0.5,
    borderBottomColor: BORDER,
    paddingVertical: 5,
    paddingHorizontal: 6,
  },
  tableRowTop: {
    flexDirection: 'row',
    borderBottomWidth: 0.5,
    borderBottomColor: BORDER,
    paddingVertical: 5,
    paddingHorizontal: 6,
    backgroundColor: '#F3F0FF',
  },
  thRank:     { width: 28,  fontSize: 7, fontFamily: 'Helvetica-Bold', color: MUTED },
  thName:     { flex: 1,    fontSize: 7, fontFamily: 'Helvetica-Bold', color: MUTED },
  thCountry:  { width: 64,  fontSize: 7, fontFamily: 'Helvetica-Bold', color: MUTED },
  thScore:    { width: 44,  fontSize: 7, fontFamily: 'Helvetica-Bold', color: MUTED, textAlign: 'right' },
  thCost:     { width: 56,  fontSize: 7, fontFamily: 'Helvetica-Bold', color: MUTED, textAlign: 'right' },
  thLead:     { width: 36,  fontSize: 7, fontFamily: 'Helvetica-Bold', color: MUTED, textAlign: 'right' },
  tdRank:     { width: 28,  fontSize: 8, color: MUTED, fontFamily: 'Helvetica-Bold' },
  tdName:     { flex: 1,    fontSize: 8, color: INK,  fontFamily: 'Helvetica-Bold' },
  tdCountry:  { width: 64,  fontSize: 8, color: MUTED },
  tdScore:    { width: 44,  fontSize: 8, color: BRAND, fontFamily: 'Helvetica-Bold', textAlign: 'right' },
  tdCost:     { width: 56,  fontSize: 8, color: INK,  textAlign: 'right' },
  tdLead:     { width: 36,  fontSize: 8, color: MUTED, textAlign: 'right' },

  // Score mini-bar inside table
  scoreMini: { flexDirection: 'row', alignItems: 'center', gap: 3, justifyContent: 'flex-end' },
  scoreMiniBarBg:   { width: 24, height: 3, backgroundColor: BORDER, borderRadius: 2 },
  scoreMiniBarFill: { height: 3, borderRadius: 2 },

  // Footer
  footer: {
    position: 'absolute',
    bottom: 24,
    left: 48,
    right: 48,
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 0.5,
    borderTopColor: BORDER,
    paddingTop: 6,
  },
  footerText: { fontSize: 7, color: MUTED },

  // Disclaimer
  disclaimer: {
    backgroundColor: SURFACE,
    borderRadius: 4,
    padding: 8,
    marginTop: 16,
  },
  disclaimerText: { fontSize: 8, color: MUTED, lineHeight: 1.5 },
});

// ── Sub-components ────────────────────────────────────────────────────────────

function BulletList({ items, warning = false }: { items: string[]; warning?: boolean }) {
  if (!items.length) return null;
  return (
    <View>
      {items.map((item, i) => (
        <View key={i} style={s.bulletRow}>
          <Text style={s.bullet}>•</Text>
          <Text style={warning ? s.bulletTextWarning : s.bulletText}>{item}</Text>
        </View>
      ))}
    </View>
  );
}

function SectionTitle({ children }: { children: string }) {
  return <Text style={s.sectionTitle}>{children}</Text>;
}

function ScoreMiniBar({ score }: { score: number }) {
  const color = score >= 70 ? SUCCESS : score >= 45 ? WARNING : '#DC2626';
  return (
    <View style={s.scoreMini}>
      <View style={s.scoreMiniBarBg}>
        <View style={[s.scoreMiniBarFill, { width: `${Math.min(score, 100)}%` as any, backgroundColor: color }]} />
      </View>
    </View>
  );
}

// ── Main document ─────────────────────────────────────────────────────────────

export function ReportPDF({ data }: { data: ReportPDFData }) {
  const confPct = Math.min(Math.max(data.confidence_score, 0), 100);
  const confColor = data.confidence_label === 'High' ? SUCCESS : data.confidence_label === 'Medium' ? WARNING : '#DC2626';

  return (
    <Document
      title={`MDC Report — ${data.project_name}`}
      author="Manufacturing Decision Copilot"
      subject="Executive Procurement Report"
      keywords="supplier, procurement, manufacturing, AI, recommendation"
    >
      <Page size="A4" style={s.page}>

        {/* ── Header ── */}
        <View style={s.header}>
          <View style={s.headerLeft}>
            <Text style={s.headerTitle}>Manufacturing Decision Copilot</Text>
            <Text style={s.headerSubtitle}>Executive Procurement Report  ·  {data.project_name}</Text>
          </View>
          <View>
            <Text style={s.headerMeta}>Generated: {data.generated_at}</Text>
            <Text style={s.headerMeta}>AI Narrative: {data.ai_narrative ? 'Yes' : 'Deterministic'}</Text>
            <Text style={s.headerMeta}>Evidence excerpts: {data.evidence_count}</Text>
          </View>
        </View>

        {/* ── Recommendation hero ── */}
        <SectionTitle>Recommendation</SectionTitle>
        <View style={s.heroCard}>
          <View style={{ flex: 1 }}>
            <Text style={s.heroBadge}>RECOMMENDED SUPPLIER</Text>
            <Text style={s.heroSupplierName}>{data.recommended_supplier_name}</Text>

            {/* Confidence bar */}
            <View style={s.confRow}>
              <Text style={{ fontSize: 8, color: MUTED, width: 70 }}>
                Confidence ({data.confidence_label})
              </Text>
              <View style={s.confBarBg}>
                <View style={[s.confBarFill, { width: `${confPct}%` as any, backgroundColor: confColor }]} />
              </View>
              <Text style={s.confLabel}>{confPct.toFixed(1)}%</Text>
            </View>
          </View>

          <View style={s.heroScoreBox}>
            <Text style={s.heroScoreLabel}>Score</Text>
            <Text style={s.heroScore}>{data.ranking[0]?.final_score.toFixed(1) ?? '—'}</Text>
            <Text style={s.heroScoreSub}>/100</Text>
          </View>
        </View>

        {/* AI badge */}
        {data.ai_narrative && (
          <View style={s.aiBadge}>
            <Text style={s.aiBadgeText}>✦ AI-Enhanced Narrative</Text>
          </View>
        )}

        {/* Summary */}
        <View style={s.summaryBox}>
          <Text style={s.summaryText}>{data.executive_summary}</Text>
        </View>

        <View style={s.summaryBox}>
          <Text style={s.colTitle}>Recommendation Statement</Text>
          <Text style={s.summaryText}>{data.recommendation_statement}</Text>
        </View>

        {/* Confidence explanation */}
        <SectionTitle>Confidence Detail</SectionTitle>
        <Text style={{ fontSize: 8, color: MUTED, lineHeight: 1.5 }}>{data.confidence_explanation}</Text>

        {/* AI Findings Grid */}
        <View style={s.twoCol}>
          <View style={s.col}>
            <Text style={s.colTitle}>Key Findings</Text>
            {data.key_findings.map((finding, i) => (
              <View key={i} style={s.bulletRow}>
                <Text style={s.bullet}>•</Text>
                <Text style={s.bulletText}>{finding}</Text>
              </View>
            ))}
          </View>

          <View style={s.col}>
            <Text style={s.colTitle}>Top Risks</Text>
            {data.risk_summary.map((risk, i) => (
              <View key={i} style={s.bulletRow}>
                <Text style={s.bullet}>•</Text>
                <Text style={s.bulletTextWarning}>{risk}</Text>
              </View>
            ))}
          </View>
        </View>

        <View style={{ marginTop: 12 }}>
          <Text style={s.colTitle}>Recommended Next Steps</Text>
          {data.next_steps.map((action, i) => (
            <View key={i} style={s.bulletRow}>
              <Text style={s.bullet}>•</Text>
              <Text style={s.bulletText}>{action}</Text>
            </View>
          ))}
        </View>

        {/* Supplier ranking table */}
        <SectionTitle>Supplier Ranking</SectionTitle>
        <View style={s.table}>
          <View style={s.tableHeader}>
            <Text style={s.thRank}>#</Text>
            <Text style={s.thName}>Supplier</Text>
            <Text style={s.thCountry}>Country</Text>
            <Text style={s.thScore}>Score</Text>
            <Text style={s.thCost}>Landed Cost</Text>
            <Text style={s.thLead}>Lead</Text>
          </View>
          {data.ranking.map((r) => (
            <View key={r.rank} style={r.rank === 1 ? s.tableRowTop : s.tableRow}>
              <Text style={s.tdRank}>#{r.rank}</Text>
              <Text style={s.tdName}>{r.supplier_name}</Text>
              <Text style={s.tdCountry}>{r.country}</Text>
              <View style={[s.tdScore as any, { justifyContent: 'flex-end' }]}>
                <Text style={s.tdScore}>{r.final_score.toFixed(1)}</Text>
                <ScoreMiniBar score={r.final_score} />
              </View>
              <Text style={s.tdCost}>${r.landed_cost.toFixed(2)}</Text>
              <Text style={s.tdLead}>{r.lead_time_days}d</Text>
            </View>
          ))}
        </View>



        {/* Disclaimer */}
        <View style={s.disclaimer}>
          <Text style={s.disclaimerText}>
            {data.disclaimer}
          </Text>
        </View>

        {/* Footer */}
        <View style={s.footer} fixed>
          <Text style={s.footerText}>Manufacturing Decision Copilot  ·  Confidential</Text>
          <Text style={s.footerText} render={({ pageNumber, totalPages }) =>
            `Page ${pageNumber} of ${totalPages}`
          } />
        </View>

      </Page>
    </Document>
  );
}
