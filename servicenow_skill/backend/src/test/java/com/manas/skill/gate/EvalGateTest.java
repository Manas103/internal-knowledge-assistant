package com.manas.skill.gate;

import com.manas.skill.corpus.CorpusGenerator;
import com.manas.skill.corpus.FrozenSeeds;
import com.manas.skill.corpus.RequestGenerator;
import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;
import com.manas.skill.retrieval.RevisionCatalog;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class EvalGateTest {

    @Test
    void theDeployedBaselineWithholdsAllOneHundredFortyEightUngroundedRequests() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);

        EvalGate.Result result = EvalGate.run(requests, corpus, RevisionCatalog.revisions().get(0));

        assertEquals(148, result.ungroundedTruthCount());
        assertEquals(148, result.ungroundedWithheldCount());
        assertEquals(result.publishedCount(), result.publishedWithResolvingCitation());
    }

    @Test
    void theDeployedBaselineCitesTheCorrectArticleForEveryPublishedGroundedDraft() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);

        EvalGate.Result result = EvalGate.run(requests, corpus, RevisionCatalog.revisions().get(0));

        assertEquals(result.groundedTruthCount(), result.publishedWithCorrectCitation());
        assertEquals(1.0, result.citationAccuracy(), 1e-9);
    }
}
