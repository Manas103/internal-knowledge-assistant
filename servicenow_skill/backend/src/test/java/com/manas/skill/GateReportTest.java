package com.manas.skill;

import com.manas.skill.corpus.CorpusGenerator;
import com.manas.skill.corpus.FrozenSeeds;
import com.manas.skill.corpus.RequestGenerator;
import com.manas.skill.domain.KnowledgeArticle;
import com.manas.skill.domain.ServiceRequest;
import com.manas.skill.gate.EvalGate;
import com.manas.skill.gate.RevisionGate;
import com.manas.skill.retrieval.RevisionCatalog;
import org.junit.jupiter.api.Test;

import java.util.List;

/**
 * Not an assertion test; prints the eval gate and deploy gate's measured numbers in a stable
 * format so they can be captured verbatim into docs/eval_gate_output.txt and
 * docs/revision_gate_output.txt. The numbers it prints are asserted precisely in
 * {@link com.manas.skill.gate.EvalGateTest} and {@link com.manas.skill.gate.RevisionGateTest}.
 */
class GateReportTest {

    @Test
    void printFrozenEvalSetReport() {
        List<KnowledgeArticle> corpus = CorpusGenerator.generate(FrozenSeeds.CORPUS_SEED);
        List<ServiceRequest> requests = RequestGenerator.generate(corpus, FrozenSeeds.REQUEST_SEED);

        System.out.println("=== Frozen eval set ===");
        System.out.println("corpus_size=" + corpus.size());
        System.out.println("total_requests=" + requests.size());
        System.out.println("grounded_truth=" + RequestGenerator.GROUNDED_COUNT);
        System.out.println("ungrounded_truth=" + RequestGenerator.UNGROUNDED_COUNT);

        List<RevisionGate.Decision> decisions = RevisionGate.run(RevisionCatalog.revisions(), requests, corpus);
        System.out.println();
        System.out.println("=== Deploy gate: revision history ===");
        System.out.printf("%-38s %10s %10s %18s %22s %9s%n",
                "revision", "acc", "blocked", "ungrounded_held", "published", "resolving");
        for (RevisionGate.Decision d : decisions) {
            EvalGate.Result r = d.result();
            System.out.printf("%-38s %10.4f %10s %18s %22d %9d%n",
                    r.config().name(), r.citationAccuracy(), d.blocked(),
                    r.ungroundedWithheldCount() + "/" + r.ungroundedTruthCount(),
                    r.publishedCount(), r.publishedWithResolvingCitation());
        }
        long blocked = RevisionGate.countBlocked(decisions);
        System.out.println();
        System.out.println("total_revisions=" + decisions.size());
        System.out.println("total_blocked=" + blocked);

        EvalGate.Result deployed = decisions.get(0).result();
        System.out.println();
        System.out.println("=== Deployed baseline (revision 1) ===");
        System.out.println("published_count=" + deployed.publishedCount());
        System.out.println("published_with_resolving_citation=" + deployed.publishedWithResolvingCitation());
        System.out.println("published_with_correct_citation=" + deployed.publishedWithCorrectCitation());
        System.out.println("citation_accuracy=" + deployed.citationAccuracy());
        System.out.println("ungrounded_withheld=" + deployed.ungroundedWithheldCount() + "/" + deployed.ungroundedTruthCount());
    }
}
