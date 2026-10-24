package com.manas.skill.gate;

import com.manas.skill.corpus.CorpusGenerator;
import com.manas.skill.corpus.FrozenSeeds;
import com.manas.skill.corpus.RequestGenerator;
import com.manas.skill.domain.Draft;
import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;
import com.manas.skill.repo.DraftRepository;
import com.manas.skill.repo.KnowledgeArticleRepository;
import com.manas.skill.repo.ServiceRequestRepository;
import com.manas.skill.retrieval.BM25Retriever;
import com.manas.skill.retrieval.RevisionCatalog;
import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * Loads the frozen synthetic corpus and eval set, runs the currently deployed retriever
 * configuration (the first revision to survive the deploy gate, which in this fixed revision
 * history is simply revision 1) over every request, and persists the resulting drafts so the
 * GraphQL review queue has real, durable rows to serve on startup.
 */
@Component
public class CorpusSeeder implements CommandLineRunner {

    private final KnowledgeArticleRepository articleRepository;
    private final ServiceRequestRepository requestRepository;
    private final DraftRepository draftRepository;

    public CorpusSeeder(KnowledgeArticleRepository articleRepository, ServiceRequestRepository requestRepository,
                         DraftRepository draftRepository) {
        this.articleRepository = articleRepository;
        this.requestRepository = requestRepository;
        this.draftRepository = draftRepository;
    }

    @Override
    public void run(String... args) {
        if (articleRepository.count() > 0) {
            return;
        }
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);
        articleRepository.saveAll(corpus);
        requestRepository.saveAll(requests);

        Map<String, KnowledgeArticle> byId = corpus.stream()
                .collect(Collectors.toMap(KnowledgeArticle::getId, Function.identity()));
        BM25Retriever retriever = new BM25Retriever(corpus, RevisionCatalog.revisions().get(0));
        DraftGenerator generator = new DraftGenerator(retriever, byId);

        for (ServiceRequest request : requests) {
            draftRepository.save(generator.draft(request));
        }
    }
}
