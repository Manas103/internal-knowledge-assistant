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
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RevisionGateTest {

    @Test
    void blocksExactlyThreeOfTheNineRevisionsForLosingCitationAccuracy() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);

        List<RevisionGate.Decision> decisions = RevisionGate.run(RevisionCatalog.revisions(), requests, corpus);

        assertEquals(9, decisions.size());
        assertEquals(3, RevisionGate.countBlocked(decisions));
        assertFalse(decisions.get(0).blocked(), "the originally deployed baseline is never itself blocked");
    }

    @Test
    void aBlockedRevisionDoesNotBecomeTheNewDeployedBaseline() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);

        List<RevisionGate.Decision> decisions = RevisionGate.run(RevisionCatalog.revisions(), requests, corpus);

        for (int i = 1; i < decisions.size(); i++) {
            RevisionGate.Decision decision = decisions.get(i);
            if (decision.blocked()) {
                assertTrue(decision.result().citationAccuracy() < decision.baselineAccuracyAtTimeOfCheck(),
                        "a blocked revision must have measured below the baseline it was checked against");
            }
        }
    }
}
