package com.manas.skill.corpus;

import com.manas.skill.domain.KnowledgeArticle;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

/**
 * Generates a synthetic, IT-service-desk-flavored knowledge base. Deterministic given a seed so
 * the frozen evaluation set below stays reproducible run to run.
 */
public final class CorpusGenerator {

    public static final int ARTICLES_PER_TOPIC = 30;

    public static final Map<String, List<String>> TOPIC_KEYWORDS = buildTopicKeywords();

    public static final List<String> TOPICS = new ArrayList<>(TOPIC_KEYWORDS.keySet());

    public static final int CORPUS_SIZE = TOPICS.size() * ARTICLES_PER_TOPIC;

    private static final List<String> FILLER = List.of(
            "the", "please", "assist", "with", "this", "request", "regarding", "our",
            "standard", "procedure", "for", "the", "service", "desk", "team", "to", "review");

    /** Scenario disambiguators: each (platform, site) pair is unique within a topic's 30 variants (6 x 5), so a request naming both narrows to exactly one article even when the topic's general keywords match many. */
    public static final List<String> PLATFORMS = List.of(
            "scnplatwindows", "scnplatmacos", "scnplatlinux", "scnplatandroid", "scnplatios", "scnplatchromeos");
    public static final List<String> SITES = List.of(
            "scnsitehomenetwork", "scnsitebranchoffice", "scnsitecampuswifi", "scnsitedatacenter", "scnsiteclientsite");

    private CorpusGenerator() {
    }

    public static List<KnowledgeArticle> generate(long seed) {
        Random random = new Random(seed);
        List<KnowledgeArticle> articles = new ArrayList<>(CORPUS_SIZE);
        int counter = 0;
        for (String topic : TOPICS) {
            List<String> keywords = TOPIC_KEYWORDS.get(topic);
            for (int variant = 0; variant < ARTICLES_PER_TOPIC; variant++) {
                String id = "KB-" + String.format("%04d", counter);
                String platform = PLATFORMS.get(variant % PLATFORMS.size());
                String site = SITES.get(variant / PLATFORMS.size());
                String title = capitalize(topic) + " (variant " + variant + ")";
                String body = buildBody(topic, keywords, variant, platform, site, random);
                articles.add(new KnowledgeArticle(id, topic, title, body, platform, site));
                counter++;
            }
        }
        return articles;
    }

    public static String platformFor(int variant) {
        return PLATFORMS.get(variant % PLATFORMS.size());
    }

    public static String siteFor(int variant) {
        return SITES.get(variant / PLATFORMS.size());
    }

    private static String buildBody(String topic, List<String> keywords, int variant, String platform,
                                      String site, Random random) {
        StringBuilder sb = new StringBuilder();
        sb.append("Knowledge article for ").append(topic.replace('-', '_')).append(". ");
        for (String keyword : keywords) {
            sb.append(keyword.replace('-', '_')).append(" ");
        }
        sb.append("Applies to ").append(platform).append(" ").append(platform)
                .append(" at ").append(site).append(" ").append(site).append(". ");
        sb.append("Variant token kbvar").append(variant).append(". ");
        int fillerCount = 3 + random.nextInt(4);
        for (int i = 0; i < fillerCount; i++) {
            sb.append(FILLER.get(random.nextInt(FILLER.size()))).append(" ");
        }
        return sb.toString().trim();
    }

    private static String capitalize(String topic) {
        String[] parts = topic.split("-");
        StringBuilder sb = new StringBuilder();
        for (String part : parts) {
            sb.append(Character.toUpperCase(part.charAt(0))).append(part.substring(1)).append(" ");
        }
        return sb.toString().trim();
    }

    private static Map<String, List<String>> buildTopicKeywords() {
        Map<String, List<String>> map = new LinkedHashMap<>();
        map.put("password-reset", List.of("password", "reset", "expired", "credential", "lockout-policy", "selfservice-portal"));
        map.put("vpn-access", List.of("vpn", "tunnel", "client-certificate", "split-tunnel", "gateway", "remote-access"));
        map.put("email-delivery", List.of("email", "bounce", "spf-record", "mailbox-quota", "smtp-relay", "distribution-list"));
        map.put("printer-setup", List.of("printer", "driver", "spooler", "network-queue", "toner", "duplex"));
        map.put("software-license", List.of("license", "seat-count", "entitlement", "activation-key", "vendor-portal", "renewal"));
        map.put("laptop-encryption", List.of("encryption", "bitlocker", "recovery-key", "tpm-chip", "disk-volume", "compliance-check"));
        map.put("wifi-connectivity", List.of("wifi", "ssid", "access-point", "signal-strength", "captive-portal", "radius-auth"));
        map.put("mobile-device-enrollment", List.of("mdm", "enrollment-profile", "compliance-policy", "byod", "passcode-policy", "remote-wipe"));
        map.put("shared-drive-permissions", List.of("shared-drive", "acl", "inherited-permission", "folder-owner", "access-request", "nested-group"));
        map.put("video-conferencing", List.of("videoconference", "webcam", "screenshare", "bandwidth", "meeting-room", "codec"));
        map.put("ticket-escalation", List.of("escalation", "priority-matrix", "sla-clock", "on-call", "major-incident", "bridge-call"));
        map.put("sso-login", List.of("sso", "saml-assertion", "identity-provider", "session-token", "federation", "login-loop"));
        map.put("mfa-enrollment", List.of("mfa", "authenticator-app", "push-approval", "backup-code", "device-binding", "otp"));
        map.put("desk-phone-setup", List.of("deskphone", "extension-number", "voicemail-box", "sip-trunk", "handset", "pbx"));
        map.put("virtual-desktop", List.of("vdi", "golden-image", "session-host", "profile-disk", "thin-client", "pool-capacity"));
        map.put("backup-restore", List.of("backup", "restore-point", "retention-schedule", "snapshot", "offsite-copy", "recovery-test"));
        map.put("antivirus-alert", List.of("antivirus", "quarantine", "signature-update", "false-positive", "endpoint-agent", "threat-definition"));
        map.put("firewall-rule-request", List.of("firewall", "ingress-rule", "port-range", "security-group", "change-window", "nat-mapping"));
        map.put("database-access-request", List.of("database", "readonly-role", "connection-string", "schema-grant", "credential-vault", "query-quota"));
        map.put("api-key-rotation", List.of("api-key", "rotation-schedule", "scope-limit", "rate-limit", "secret-store", "revocation"));
        map.put("cloud-storage-quota", List.of("cloudstorage", "quota-limit", "bucket-policy", "lifecycle-rule", "archive-tier", "egress-cost"));
        map.put("calendar-sync", List.of("calendar", "sync-token", "free-busy", "timezone-mismatch", "recurring-event", "delegate-access"));
        map.put("browser-extension-approval", List.of("browser-extension", "allowlist", "manifest-permission", "sandbox-policy", "update-channel", "store-review"));
        map.put("remote-desktop", List.of("rdp", "gateway-broker", "idle-timeout", "clipboard-redirect", "multi-monitor", "session-limit"));
        map.put("network-drive-mapping", List.of("drive-mapping", "login-script", "unc-path", "dfs-namespace", "offline-files", "quota-warning"));
        map.put("spam-filter-tuning", List.of("spam-filter", "allowlist-domain", "phishing-report", "quarantine-digest", "bulk-mail-rule", "dmarc-policy"));
        map.put("account-lockout", List.of("account-lockout", "failed-attempt", "unlock-request", "threshold-policy", "brute-force-alert", "identity-verification"));
        map.put("group-membership-request", List.of("group-membership", "approval-chain", "owner-signoff", "nested-role", "access-review", "expiry-date"));
        map.put("patch-deployment", List.of("patch", "maintenance-window", "rollback-plan", "compliance-scan", "reboot-required", "staged-ring"));
        map.put("asset-tagging", List.of("asset-tag", "barcode-scan", "depreciation-schedule", "inventory-audit", "serial-number", "disposal-record"));
        map.put("onboarding-checklist", List.of("onboarding", "day-one-access", "equipment-request", "badge-provisioning", "orientation", "manager-approval"));
        map.put("offboarding-checklist", List.of("offboarding", "access-revocation", "equipment-return", "data-retention", "exit-interview", "forwarding-rule"));
        map.put("license-compliance-audit", List.of("compliance-audit", "true-up", "overdeployment", "usage-report", "vendor-notice", "reconciliation"));
        map.put("change-request-approval", List.of("change-request", "cab-review", "risk-assessment", "rollback-window", "implementation-plan", "post-change-review"));
        map.put("incident-priority-override", List.of("priority-override", "business-impact", "vip-flag", "manager-escalation", "justification-note", "re-triage"));
        map.put("service-catalog-item", List.of("catalog-item", "fulfillment-workflow", "variable-set", "approval-definition", "record-producer", "cart-checkout"));
        map.put("knowledge-article-review", List.of("article-review", "retirement-date", "owner-group", "feedback-rating", "revision-history", "flagged-outdated"));
        map.put("sla-breach-notification", List.of("sla-breach", "breach-notification", "pause-condition", "workflow-timer", "escalation-rule", "contract-clause"));
        map.put("chatbot-handoff", List.of("chatbot", "handoff-trigger", "intent-confidence", "live-agent-queue", "conversation-transcript", "fallback-response"));
        map.put("data-export-request", List.of("data-export", "retention-policy", "approval-required", "format-option", "pii-redaction", "delivery-method"));
        return map;
    }
}
