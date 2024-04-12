#include <stddef.h>
#include <string.h>
#include <stdbool.h>

#include "loader.h"

int spins_get_state_size();
int spins_get_transition_groups();
void spins_get_initial_state(int *dst);
int spins_get_successor_all(void *model, int *src, void *callback, void *usr);

// type info
char *spins_get_state_variable_name(int var);
int spins_get_state_variable_type(int var);
char *spins_get_type_name(int type);
int spins_get_type_count();
char *spins_get_type_value_name(int type, int value);
int spins_get_type_value_count(int type);

// edge labels
int spins_get_edge_count();
char *spins_get_edge_name(int type);
int spins_get_edge_type(int type);

// state labels
int spins_get_label_count();
int spins_get_guard_count();
int *spins_get_label_matrix(int g);

int *spins_get_labels(int t);
int **spins_get_all_labels();
int spins_get_label(void *, int g, int *src);
char *spins_get_label_name(int g);
void spins_get_labels_many(void *model, int *src, int *labels,
                           bool guards_only);

void _spins_get_label_all(void *model, int *src, int *labels){
  spins_get_labels_many(model, src, labels, false);
}

// reduction information
int *spins_get_trans_do_not_accord_matrix(int t);
int *spins_get_label_nes_matrix(int g);
int *spins_get_label_nds_matrix(int g);

int *spins_get_trans_commutes_matrix(int t);
int *spins_get_label_may_be_coenabled_matrix(int g);

int *spins_get_transition_read_dependencies(int t);
int *spins_get_transition_may_write_dependencies(int t);
int *spins_get_transition_must_write_dependencies(int t);
int *spins_get_actions_read_dependencies(int t);

struct Matrix matrices[0x20];
static void matrixConvert(int n, int m, int *(*_spins_get_matrix)(int r),
                          void (*_GBsetMatrix)(void *mdl, struct Matrix *mtx)){
  // Convert a [n]x[m] matrix received from [_spins_get_matrix] into one
  //  suitable for [_GBsetMatrix].
  static int mid = 0;
  struct Matrix *mtx = &matrices[mid++];

  if((*_spins_get_matrix)(0)==NULL)
    return;

  dm_create(mtx, n, m);
  for(int i = 0; i < n; i++){
    int *row = (*_spins_get_matrix)(i);
    if(row==NULL)
      continue;

    for(int j = 0; j < m; j++){
      if(row[j])
        dm_set(mtx, i, j);
    }
  }
  (*_GBsetMatrix)(NULL, mtx);
}

void pins_model_init(void){
  // PINS loader for SpinS models.

  // set state names and types
  int slots = spins_get_state_size();
  lts_type_set_state_length(NULL, slots);

  for(int i = 0; i < slots; i++){
    lts_type_set_state_name(NULL, i, spins_get_state_variable_name(i));
    // XXX: we currently assume all types are int
  }

  // create edge label types
  int types = spins_get_type_count();
  for(int i = 0; i < types; i++){
    char *name = spins_get_type_name(i);
    lts_type_add_type(NULL, name, NULL);

    int chunks = spins_get_type_value_count(i);
    for(int j = 0; j < chunks; j++){
      char *chunk = spins_get_type_value_name(i, j);
      GBchunkPut(NULL, i, (struct Chunk){strlen(chunk), chunk});
    }
  }

  // set edge label types
  int actionLabel = -1;
  int edges = spins_get_edge_count();
  lts_type_set_edge_label_count(NULL, edges);
  for(int i = 0; i < edges; i++){
    lts_type_set_edge_label_name(NULL, i, spins_get_edge_name(i));

    int type = spins_get_edge_type(i);
    lts_type_set_edge_label_typeno(NULL, i, type);

    // "statement" is the action label
    if(strcmp(spins_get_type_name(type), "statement")==0)
      actionLabel = i;
  }

  if(actionLabel >= 0)
    _wrapperSetActionLabel(actionLabel);

  // set initial state
  int state[slots];
  spins_get_initial_state(state);
  GBsetInitialState(NULL, state);

  // set successor functions
  GBsetNextStateAll(NULL, (void (*)())&spins_get_successor_all);

  // set state label names and types
  int labels = spins_get_label_count();
  lts_type_set_state_label_count(NULL, labels);
  for(int i = 0; i < labels; i++){
    char *name = spins_get_label_name(i);
    lts_type_set_state_label_name(NULL, i, name);
  }

  // set state labeling function
  GBsetStateLabelLong(NULL, (StateLabelLongFn) &spins_get_label);
  GBsetStateLabelsAll(NULL, (StateLabelAllFn) &_spins_get_label_all);

  // set up guards
  int actions = spins_get_transition_groups();
  _wrapperSetActionCount(actions);

  GBsetGuardsInfo(NULL, (struct Guard **)spins_get_all_labels());

  // set up reduction information
  matrixConvert(actions, actions,
                spins_get_trans_do_not_accord_matrix,
                GBsetDoNotAccordInfo);

  matrixConvert(labels, actions,
                spins_get_label_nes_matrix,
                GBsetGuardNESInfo);
  matrixConvert(labels, actions,
                spins_get_label_nds_matrix,
                GBsetGuardNDSInfo);

  matrixConvert(actions, actions,
                spins_get_trans_commutes_matrix,
                GBsetCommutesInfo);
  matrixConvert(labels, labels,
                spins_get_label_may_be_coenabled_matrix,
                GBsetGuardCoEnabledInfo);

  // set up affect sets
  matrixConvert(actions, slots,
                spins_get_transition_read_dependencies,
                GBsetDMInfoRead);
  matrixConvert(actions, slots,
                spins_get_transition_may_write_dependencies,
                GBsetDMInfoMayWrite);
  matrixConvert(actions, slots,
                spins_get_transition_must_write_dependencies,
                GBsetDMInfoMustWrite);

  matrixConvert(labels, slots,
                spins_get_label_matrix,
                GBsetStateLabelInfo);
}
