package com.manas.skill.retrieval;

import com.manas.skill.domain.KnowledgeArticle;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * BM25 ranking over the synthetic knowledge base, with a slow brute-force reference
 * implementation ({@link #scoreBruteForce}) kept separate from the indexed fast path so the two
 * can be diffed exactly in tests.
 */
public final class BM25Retriever {

    public record Match(KnowledgeArticle article, double score, double confidence) {
    }

    private final RetrieverConfig config;
    private final List<KnowledgeArticle> corpus;
    private final List<Map<String, Integer>> termFrequencies;
    private final Map<String, Integer> documentFrequency;
    private final double averageDocLength;
    private final double[] docLengths;

    public BM25Retriever(List<KnowledgeArticle> corpus, RetrieverConfig config) {
        this.config = config;
        this.corpus = corpus;
        this.termFrequencies = new ArrayList<>(corpus.size());
        this.documentFrequency = new HashMap<>();
        this.docLengths = new double[corpus.size()];

        double totalLength = 0;
        for (int i = 0; i < corpus.size(); i++) {
            KnowledgeArticle article = corpus.get(i);
            List<String> tokens = Tokenizer.tokenize(boosted(article), config);
            Map<String, Integer> tf = new HashMap<>();
            for (String token : tokens) {
                tf.merge(token, 1, Integer::sum);
            }
            termFrequencies.add(tf);
            docLengths[i] = tokens.size();
            totalLength += tokens.size();
            for (String term : tf.keySet()) {
                documentFrequency.merge(term, 1, Integer::sum);
            }
        }
        this.averageDocLength = corpus.isEmpty() ? 0 : totalLength / corpus.size();
    }

    /**
     * The human-readable {@code title} field is display-only and deliberately excluded from the
     * index: it spells topic words out in plain English ("Email Delivery"), which would leak
     * generic dictionary words into the corpus vocabulary and let an out-of-domain request match
     * on a stray word match alone. The title boost instead repeats the same compounded topic
     * token the body already carries, so boosting cannot introduce vocabulary the body lacks.
     */
    private String boosted(KnowledgeArticle article) {
        String topicToken = article.getTopic().replace('-', '_');
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < config.titleBoost(); i++) {
            sb.append(topicToken).append(" ");
        }
        sb.append(article.getBody());
        return sb.toString();
    }

    private double idf(String term) {
        int df = documentFrequency.getOrDefault(term, 0);
        double n = corpus.size();
        return Math.log(1 + (n - df + 0.5) / (df + 0.5));
    }

    public Match topMatch(String requestText) {
        List<String> queryTokens = Tokenizer.tokenize(requestText, config);
        double bestScore = Double.NEGATIVE_INFINITY;
        KnowledgeArticle best = null;

        for (int i = 0; i < corpus.size(); i++) {
            double score = scoreIndexed(queryTokens, i);
            if (score > bestScore) {
                bestScore = score;
                best = corpus.get(i);
            }
        }
        double confidence = bestScore <= 0 ? 0.0 : bestScore / (bestScore + 6.0);
        return new Match(best, Math.max(bestScore, 0.0), confidence);
    }

    /** Exposed so tests can diff the indexed path against {@link #scoreBruteForce} per document. */
    public double scoreIndexedForArticle(String requestText, KnowledgeArticle article) {
        int docIndex = corpus.indexOf(article);
        return scoreIndexed(Tokenizer.tokenize(requestText, config), docIndex);
    }

    private double scoreIndexed(List<String> queryTokens, int docIndex) {
        Map<String, Integer> tf = termFrequencies.get(docIndex);
        double length = docLengths[docIndex];
        double score = 0.0;
        for (String term : queryTokens) {
            int freq = tf.getOrDefault(term, 0);
            if (freq == 0) {
                continue;
            }
            double idf = idf(term);
            double numerator = freq * (config.k1() + 1);
            double denominator = freq + config.k1() * (1 - config.b() + config.b() * length / averageDocLength);
            score += idf * (numerator / denominator);
        }
        return score;
    }

    /** Deliberately slow, obviously-correct re-derivation of the same formula, recomputing term frequencies from scratch for the single document under test rather than reading the prebuilt index. Diffed exactly against {@link #topMatch} in tests. */
    public double scoreBruteForce(String requestText, KnowledgeArticle article) {
        List<String> queryTokens = Tokenizer.tokenize(requestText, config);
        List<String> docTokens = Tokenizer.tokenize(boosted(article), config);
        Map<String, Integer> tf = new HashMap<>();
        for (String token : docTokens) {
            tf.merge(token, 1, Integer::sum);
        }
        double length = docTokens.size();
        double score = 0.0;
        for (String term : queryTokens) {
            int freq = tf.getOrDefault(term, 0);
            if (freq == 0) {
                continue;
            }
            double idf = idf(term);
            double numerator = freq * (config.k1() + 1);
            double denominator = freq + config.k1() * (1 - config.b() + config.b() * length / averageDocLength);
            score += idf * (numerator / denominator);
        }
        return score;
    }
}
