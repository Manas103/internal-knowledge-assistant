package com.manas.skill.gate;

import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;
import com.manas.skill.retrieval.RetrieverConfig;

import java.util.ArrayList;
import java.util.List;

/**
 * The deploy-blocking evaluator. Walks the revision history in order, keeping track of the
 * currently deployed configuration's citation accuracy on the frozen eval set. A later revision
 * is blocked, and the deployed baseline left unchanged, if its measured citation accuracy is
 * lower than the currently deployed baseline's; otherwise it becomes the new baseline. This is
 * run offline over historical configs here, not a live CI hook, but the decision rule is the one
 * a real pre-deploy gate would apply.
 */
public final class RevisionGate {

    public record Decision(EvalGate.Result result, boolean blocked, double baselineAccuracyAtTimeOfCheck) {
    }

    public static List<Decision> run(List<RetrieverConfig> revisionsInOrder, List<ServiceRequest> requests,
                                       List<KnowledgeArticle> corpus) {
        List<Decision> decisions = new ArrayList<>();
        double deployedAccuracy = -1.0;

        for (RetrieverConfig config : revisionsInOrder) {
            EvalGate.Result result = EvalGate.run(requests, corpus, config);
            if (deployedAccuracy < 0) {
                // First revision is the originally deployed baseline; nothing to gate it against.
                deployedAccuracy = result.citationAccuracy();
                decisions.add(new Decision(result, false, result.citationAccuracy()));
                continue;
            }
            boolean blocked = result.citationAccuracy() < deployedAccuracy;
            decisions.add(new Decision(result, blocked, deployedAccuracy));
            if (!blocked) {
                deployedAccuracy = result.citationAccuracy();
            }
        }
        return decisions;
    }

    public static long countBlocked(List<Decision> decisions) {
        return decisions.stream().filter(Decision::blocked).count();
    }
}
