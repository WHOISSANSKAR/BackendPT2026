-- changes done by vb: Minutes of Meeting (MOM) tables.
-- The admin records each project meeting (what was discussed, changes agreed to locations,
-- milestones, tasks) and the customer sees it read-only via
--   GET /api/v1/customer/projects/{project_id}/moms
--
-- Multi-value text fields (attendees, agenda) store ONE ENTRY PER LINE.
-- Dates are stored as 'YYYY-MM-DD' strings, like the rest of this schema.
-- Safe to run more than once (IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS `project_mom` (
  `pmom_id`                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `pmom_project_id`        BIGINT UNSIGNED NOT NULL,          -- project_list.plist_id
  `pmom_scope_id`          BIGINT UNSIGNED NULL DEFAULT NULL, -- project_scope.pscope_id (location), optional
  `pmom_phase`             VARCHAR(255)    NULL DEFAULT NULL,
  `pmom_milestone`         VARCHAR(255)    NULL DEFAULT NULL,
  `pmom_task`              VARCHAR(255)    NULL DEFAULT NULL,
  `pmom_prepared_by`       VARCHAR(255)    NOT NULL,
  `pmom_prepared_on`       VARCHAR(20)     NOT NULL,          -- meeting date, YYYY-MM-DD
  `pmom_meeting_type`      VARCHAR(100)    NULL DEFAULT NULL, -- e.g. Site review, Kick-off, Weekly sync
  `pmom_attendees_present` TEXT            NULL,              -- one name per line
  `pmom_attendees_absent`  TEXT            NULL,              -- one name per line
  `pmom_agenda`            TEXT            NULL,              -- one agenda item per line
  `pmom_summary`           TEXT            NULL,
  `pmom_next_meeting`      VARCHAR(20)     NULL DEFAULT NULL, -- YYYY-MM-DD
  `pmom_created_by_pt_id`  BIGINT          NULL DEFAULT NULL, -- admin (weusers.id) who recorded it
  `created_at`             VARCHAR(20)     NULL DEFAULT NULL,
  `updated_at`             VARCHAR(20)     NULL DEFAULT NULL,
  PRIMARY KEY (`pmom_id`),
  KEY `idx_pmom_project` (`pmom_project_id`),
  KEY `idx_pmom_scope` (`pmom_scope_id`),
  CONSTRAINT `fk_pmom_project` FOREIGN KEY (`pmom_project_id`)
    REFERENCES `project_list` (`plist_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `project_mom_action_items` (
  `pmomact_id`       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `pmomact_mom_id`   BIGINT UNSIGNED NOT NULL,                -- project_mom.pmom_id
  `pmomact_action`   VARCHAR(500)    NOT NULL,
  `pmomact_owner`    VARCHAR(255)    NULL DEFAULT NULL,
  `pmomact_due_date` VARCHAR(20)     NULL DEFAULT NULL,       -- YYYY-MM-DD
  `pmomact_status`   VARCHAR(50)     NOT NULL DEFAULT 'Open', -- Open / In Progress / Done / Cancelled
  `pmomact_sort`     INT             NOT NULL DEFAULT 0,      -- display order (# column)
  `created_at`       VARCHAR(20)     NULL DEFAULT NULL,
  `updated_at`       VARCHAR(20)     NULL DEFAULT NULL,
  PRIMARY KEY (`pmomact_id`),
  KEY `idx_pmomact_mom` (`pmomact_mom_id`),
  CONSTRAINT `fk_pmomact_mom` FOREIGN KEY (`pmomact_mom_id`)
    REFERENCES `project_mom` (`pmom_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
