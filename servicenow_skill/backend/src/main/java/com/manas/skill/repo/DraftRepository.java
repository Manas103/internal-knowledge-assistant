package com.manas.skill.repo;

import com.manas.skill.domain.Draft;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface DraftRepository extends JpaRepository<Draft, Long> {

    List<Draft> findByStatus(String status);
}
