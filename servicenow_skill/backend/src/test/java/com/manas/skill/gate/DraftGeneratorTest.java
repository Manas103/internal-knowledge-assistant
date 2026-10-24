package com.manas.skill.gate;

import com.manas.skill.corpus.CorpusGenerator;
import com.manas.skill.corpus.FrozenSeeds;
import com.manas.skill.corpus.RequestGenerator;
import com.manas.skill.domain.Draft;
import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;
import com.manas.skill.retrieval.BM25Retriever;
import com.manas.skill.retrieval.RevisionCatalog;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.assertTrue;

class DraftGeneratorTest {

    @Test
    void everyPublishedDraftCitesAnArticleThatActuallyResolves() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);
        Map<String, KnowledgeArticle> byId = corpus.stream()
                .collect(Collectors.toMap(KnowledgeArticle::getId, Function.identity()));
        BM25Retriever retriever = new BM25Retriever(corpus, RevisionCatalog.revisions().get(0));
        DraftGenerator generator = new DraftGenerator(retriever, byId);

        int published = 0;
        for (ServiceRequest request : requests) {
            Draft draft = generator.draft(request);
            if (draft.isGrounded()) {
                published++;
                assertTrue(byId.containsKey(draft.getCitedArticleId()),
                        "published draft cited an article id that does not resolve: " + draft.getCitedArticleId());
            }
        }
        assertTrue(published > 0, "sanity: at least some drafts should have been published");
    }

    @Test
    void refusesToConstructAGroundedDraftForAnUnknownArticleId() {
        // DraftGenerator.draft() is defensive: it only ever cites an id that came back from the
        // retriever's own corpus, so the only way to exercise the failure path is to call it with
        // a retriever whose article map excludes the id it will return.
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);
        BM25Retriever retriever = new BM25Retriever(corpus, RevisionCatalog.revisions().get(0));
        DraftGenerator generator = new DraftGenerator(retriever, Map.of());

        ServiceRequest groundedRequest = requests.stream()
                .filter(r -> r.getTrueArticleId() != null)
                .findFirst().orElseThrow();

        try {
            generator.draft(groundedRequest);
        } catch (IllegalStateException expected) {
            return;
        }
        throw new AssertionError("expected an IllegalStateException when the cited article cannot resolve");
    }
}
