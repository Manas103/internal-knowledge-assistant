package com.manas.skill.retrieval;

import java.util.List;

/**
 * Nine historical prompt/retriever revisions, in deployment order. Revision 1 is the originally
 * deployed baseline; each later revision is a real change someone proposed (stemming, bigram
 * matching, dropping the title boost, and so on). The deploy gate in {@link
 * com.manas.skill.gate.RevisionGate} measures each against the frozen eval set before deciding
 * whether it becomes the new deployed baseline.
 */
public final class RevisionCatalog {

    private RevisionCatalog() {
    }

    public static List<RetrieverConfig> revisions() {
        return List.of(
                new RetrieverConfig("rev1-baseline", 1.5, 0.75, 2.0, 3, true, false, false, false),
                new RetrieverConfig("rev2-add-stemming", 1.5, 0.75, 2.0, 3, true, true, false, false),
                new RetrieverConfig("rev3-keep-stopwords", 1.5, 0.75, 2.0, 3, false, true, false, false),
                new RetrieverConfig("rev4-add-bigrams", 1.5, 0.75, 2.0, 3, true, true, true, false),
                new RetrieverConfig("rev5-raise-k1", 3.0, 0.75, 2.0, 3, true, true, true, false),
                new RetrieverConfig("rev6-strip-scenario-tokens-as-noise", 1.5, 0.75, 2.0, 3, true, true, true, true),
                new RetrieverConfig("rev7-overtighten-min-token-length", 1.5, 0.75, 2.0, 20, true, true, true, false),
                new RetrieverConfig("rev8-drop-title-boost", 1.5, 0.75, 1.0, 3, true, true, true, false),
                new RetrieverConfig("rev9-combined-best", 1.5, 0.75, 3.0, 3, true, true, true, false));
    }
}
