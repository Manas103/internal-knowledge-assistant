package com.manas.skill.gate;

import com.manas.skill.domain.Draft;
import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;
import com.manas.skill.retrieval.BM25Retriever;
import com.manas.skill.retrieval.RetrieverConfig;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * Runs the full frozen eval set through a given retriever configuration and reports the numbers
 * the deploy gate and the resume both depend on: how many ungrounded requests were correctly
 * withheld, how many grounded requests were published with the right citation, and whether every
 * published draft's citation actually resolves.
 */
public final class EvalGate {

    public record Result(
            RetrieverConfig config,
            int totalRequests,
            int groundedTruthCount,
            int ungroundedTruthCount,
            int ungroundedWithheldCount,
            int publishedCount,
            int publishedWithResolvingCitation,
            int publishedWithCorrectCitation,
            double citationAccuracy) {
    }

    public static Result run(List<ServiceRequest> requests, List<KnowledgeArticle> corpus, RetrieverConfig config) {
        BM25Retriever retriever = new BM25Retriever(corpus, config);
        Map<String, KnowledgeArticle> byId = corpus.stream()
                .collect(Collectors.toMap(KnowledgeArticle::getId, Function.identity()));
        DraftGenerator generator = new DraftGenerator(retriever, byId);

        int groundedTruth = 0;
        int ungroundedTruth = 0;
        int ungroundedWithheld = 0;
        int published = 0;
        int publishedResolving = 0;
        int publishedCorrect = 0;

        for (ServiceRequest request : requests) {
            Draft draft = generator.draft(request);
            boolean isGroundedTruth = request.getTrueArticleId() != null;
            if (isGroundedTruth) {
                groundedTruth++;
            } else {
                ungroundedTruth++;
                if (!draft.isGrounded()) {
                    ungroundedWithheld++;
                }
            }
            if (draft.isGrounded()) {
                published++;
                if (byId.containsKey(draft.getCitedArticleId())) {
                    publishedResolving++;
                }
                if (isGroundedTruth && draft.getCitedArticleId().equals(request.getTrueArticleId())) {
                    publishedCorrect++;
                }
            }
        }

        double citationAccuracy = groundedTruth == 0 ? 0.0 : (double) publishedCorrect / groundedTruth;

        return new Result(config, requests.size(), groundedTruth, ungroundedTruth, ungroundedWithheld,
                published, publishedResolving, publishedCorrect, citationAccuracy);
    }
}
