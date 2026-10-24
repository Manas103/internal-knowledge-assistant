package com.manas.skill.retrieval;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public final class Tokenizer {

    public static final Set<String> STOPWORDS = Set.of(
            "the", "a", "an", "and", "or", "with", "for", "to", "of", "in", "on", "is", "are",
            "this", "that", "please", "assist", "our", "standard", "procedure", "service", "desk",
            "team", "review", "regarding", "request", "about", "mentions", "same", "asks", "reports",
            "trouble", "help", "related", "user");

    private Tokenizer() {
    }

    public static List<String> tokenize(String text, RetrieverConfig config) {
        List<String> raw = List.of(text.toLowerCase().split("[^a-z0-9_]+"));
        List<String> tokens = new ArrayList<>();
        for (String token : raw) {
            if (token.isBlank() || token.length() < config.minTokenLength()) {
                continue;
            }
            if (config.removeStopwords() && STOPWORDS.contains(token)) {
                continue;
            }
            if (config.ignoreScenarioTokens() && (token.startsWith("scnplat") || token.startsWith("scnsite"))) {
                continue;
            }
            tokens.add(config.stemming() ? stem(token) : token);
        }
        if (config.bigramBoost()) {
            int unigramCount = tokens.size();
            for (int i = 0; i + 1 < unigramCount; i++) {
                tokens.add(tokens.get(i) + "_" + tokens.get(i + 1));
            }
        }
        return tokens;
    }

    /** Deliberately crude suffix-stripping stemmer, not a linguistic one; good enough to fold plural/verb variants together. */
    private static String stem(String token) {
        if (token.endsWith("ies") && token.length() > 5) {
            return token.substring(0, token.length() - 3) + "y";
        }
        if (token.endsWith("es") && token.length() > 4) {
            return token.substring(0, token.length() - 2);
        }
        if (token.endsWith("s") && !token.endsWith("ss") && token.length() > 3) {
            return token.substring(0, token.length() - 1);
        }
        return token;
    }
}
