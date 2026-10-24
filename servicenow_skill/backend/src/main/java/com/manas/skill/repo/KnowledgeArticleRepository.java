package com.manas.skill.repo;

import com.manas.skill.domain.KnowledgeArticle;
import org.springframework.data.jpa.repository.JpaRepository;

public interface KnowledgeArticleRepository extends JpaRepository<KnowledgeArticle, String> {
}
