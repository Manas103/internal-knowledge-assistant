package com.manas.skill.retrieval;

/**
 * One historical configuration of the retriever. Each named revision in {@link RevisionCatalog}
 * is one of these; the deploy gate measures citation accuracy for each against the frozen eval
 * set before a revision is allowed to become the deployed baseline.
 */
public record RetrieverConfig(
        String name,
        double k1,
        double b,
        double titleBoost,
        int minTokenLength,
        boolean removeStopwords,
        boolean stemming,
        boolean bigramBoost,
        boolean ignoreScenarioTokens) {

    public static RetrieverConfig baseline(String name) {
        return new RetrieverConfig(name, 1.5, 0.75, 2.0, 3, true, false, false, false);
    }
}
