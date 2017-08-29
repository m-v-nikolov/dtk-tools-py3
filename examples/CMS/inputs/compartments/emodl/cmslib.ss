(library (emodl cmslib)
    (export start-model json config param func bool state-event time-event species observe reaction locale set-locale end-model set-loglevel)
    ;(export get-builder get-model get-model-name)
    (import (rnrs) (ironscheme) (ironscheme conversions) (ironscheme clr) (emodl cmsexpressions))

(clr-reference compartments)
(clr-using compartments)
(clr-using compartments.emod)
(clr-using compartments.emod.interfaces)
(clr-using compartments.emod.expressions)
(clr-using compartments.solvers)
(clr-using compartments.emodl)

(define *loglevel* 1)

(define (set-loglevel level)
	(set! *loglevel* level)
)

(define (do-writelog level contents)
	(if (>= *loglevel* level)
		(begin
			(for-each display contents)
			(newline)
		)
	)
)

(define-syntax writelog
	(syntax-rules ()
		[(_ contents)       (do-writelog 0     contents)]
		[(_ level contents) (do-writelog level contents)]
	)
)

(define *model*)
(define *builder*)
(define *current-locale*)

(define (get-builder)
    *builder*)

(define (get-model)
    *model*)
    
(define (get-locale)
    *current-locale*)

(define (get-model-name)
    (clr-call ModelInfo get_Name *model*))

(define (start-model name)
	(writelog `("Parsing model '" ,name "'..."))
    ;(display "Parsing model ") (display name) (newline)
    (set! *builder* (clr-new ModelInfo+ModelBuilder name))
    (set! *model* (clr-call ModelInfo+ModelBuilder get_Model *builder*))
    (set! *current-locale* (clr-new LocaleInfo "global"))
    (clr-call ModelInfo+ModelBuilder AddLocale *builder* *current-locale*)
    (def-parameter  'time 0.0)
    (def-parameter  'pi 3.14159265)
    (def-expression 'rand '(rand))
)

(define (end-model)
	(writelog `("...finished parsing '" ,(get-model-name) "'."))
    (clr-static-field-set! EmodlLoader modelInfo *model*))

(define (def-locale name)
    (clr-call ModelInfo+ModelBuilder AddLocale *builder* (clr-new LocaleInfo (symbol->string name)))
	(writelog 1 '("Added locale '" name "'."))
)

(define-syntax locale
    (syntax-rules ()
        ((_ name) (def-locale 'name))
    )
)

(define (set-locale! name)
	(let ((locale-name (symbol->string name)))
		(set! *current-locale* (clr-call ModelInfo GetLocaleByName *model* locale-name))
		(writelog 1 `("Current locale: " ,locale-name))
	)
)

(define-syntax set-locale
    (syntax-rules ()
        ((_ name) (set-locale! 'name))
    )
)

(define (def-parameter symbol expression)
	(writelog 2 `("def-parameter " ,symbol " " ,expression))
    (let* ((value (real->flonum (if (number? expression) expression (eval expression (environment '(rnrs))))))
           (new-param (clr-new ParameterInfo (symbol->string symbol) (->single value))))

       (clr-call ModelInfo+ModelBuilder AddParameter *builder* new-param)
	   (writelog 1 `("New parameter: " ,symbol " = " ,value))
       value
    )
)

(define-syntax param
    (syntax-rules ()
        [(_ name expression)
            (define name (def-parameter 'name expression))]))

(define (def-expression name expression)
    (let ((new-net (clr-new NumericExpressionTree (symbol->string name) (parse-expression expression))))
        (clr-call ModelInfo+ModelBuilder AddExpression (get-builder) new-net)
        new-net
    )
)

(define (def-anon-expression expression)
    (let ((new-net (clr-new NumericExpressionTree (parse-expression expression))))
        (clr-call ModelInfo+ModelBuilder AddExpression (get-builder) new-net)
		(writelog 2 `("New anonymous expression: " ,expression))
        new-net
    )
)

(define-syntax func
    (syntax-rules ()
        [(_ symbol expression)
            (def-expression 'symbol 'expression)]))

(define (def-predicate name expression)
    (let* ((expression-name (if (symbol? name) (symbol->string name) name))
           (new-bet (clr-new BooleanExpressionTree expression-name (parse-boolean expression))))

        (clr-call ModelInfo+ModelBuilder AddPredicate *builder* new-bet)
        new-bet
    )
)
            
(define-syntax bool
    (syntax-rules ()
        [(_ symbol expression)
            (def-predicate 'symbol 'expression)
        ]
    )
)

(define (def-time-event name time interval actions)
    (let* ((event-name (if (symbol? name) (symbol->string name) name))
           (event-time (->single (real->flonum (if (number? time) time (eval time (environment '(rnrs)))))))
           (event-interval (->single (real->flonum (if (number? interval) interval (eval interval (environment '(rnrs)))))))
           (event-builder (clr-new ScheduledEventInfo+Builder event-name))
           )

		(writelog 2 `("(time-event " ,name " " ,time " " ,interval " " ,actions ")"))
           
        (clr-call ScheduledEventInfo+Builder SetTime event-builder event-time)
        (clr-call ScheduledEventInfo+Builder SetInterval event-builder event-interval)
        (for-each
            (lambda (a) 
                (clr-call ScheduledEventInfo+Builder AddAction event-builder
                    (clr-new TargetReference (symbol->string (car a)))
                    (clr-new NumericExpressionTree (parse-expression (cadr a)))))
            actions
        )
        (clr-call ModelInfo+ModelBuilder AddScheduledEvent *builder* (clr-call ScheduledEventInfo+Builder get_Event event-builder))
    )
)

(define-syntax time-event
    (syntax-rules ()
        [(_ symbol time actions)
            (def-time-event 'symbol time 0 'actions)
        ]
        [(_ symbol time interval actions)
            (def-time-event 'symbol time interval 'actions)
        ]
    )
)
(define (def-state-event name predicate actions)
    (let* ((event-name (if (symbol? name) (symbol->string name) name))
           (event-predicate (clr-new BooleanExpressionTree (parse-boolean predicate)))
           (event-builder (clr-new TriggeredEventInfo+Builder event-name)))

        (clr-call TriggeredEventInfo+Builder SetPredicate event-builder event-predicate)
        (for-each
            (lambda (a) 
                (clr-call TriggeredEventInfo+Builder AddAction event-builder
                    (clr-new TargetReference (symbol->string (car a)))
                    (clr-new NumericExpressionTree (parse-expression (cadr a)))))
            actions
        )
        (clr-call ModelInfo+ModelBuilder AddTriggeredEvent *builder* (clr-call TriggeredEventInfo+Builder get_Event event-builder))
    )
)

(define-syntax state-event
    (syntax-rules ()
        [(_ symbol predicate actions)
            (def-state-event 'symbol 'predicate 'actions)
        ]
    )
)

(define (def-species symbol initial)
    ; (display "Number?   ") (display (number?   initial)) (newline)
    ; (display "Complex?  ") (display (complex?  initial)) (newline)
    ; (display "Real?     ") (display (real?     initial)) (newline)
    ; (display "Rational? ") (display (rational? initial)) (newline)
    ; (display "Integer?  ") (display (integer?  initial)) (newline)
    ; (display "New species: ") (display symbol) (display "[") (display (round initial)) (display "]") (newline)
;    (let* ((trunc   (exact (round initial)))
;           (species (clr-new SpeciesDescription (symbol->string symbol) trunc (get-locale))))
;
;        (clr-call ModelInfo+ModelBuilder AddSpecies *builder* species)
;    )
	(let* ((new-net (def-anon-expression initial))
		(species (clr-new SpeciesDescription (symbol->string symbol) new-net (get-locale))))
		;(species (clr-new SpeciesDescription (symbol->string symbol) 0 (get-locale))))
		;(writelog 2 '("Calling ModeInfo+ModelBuilder.AddSpecies()..."))
		(clr-call ModelInfo+ModelBuilder AddSpecies *builder* species)
		(writelog 1 `("New species: '" ,(symbol->string symbol) "'"))
	)
)

(define-syntax species
    (syntax-rules ()
        [(_ symbol)
            (def-species 'symbol 0)]
        [(_ symbol initial)
            (def-species 'symbol 'initial)]))

(define (def-observable symbol expression)
    (let ((new-observable (clr-new ObservableInfo (symbol->string symbol) (def-anon-expression expression))))

        (clr-call ModelInfo+ModelBuilder AddObservable *builder* new-observable)
        new-observable
    )
)

(define-syntax observe
    (syntax-rules ()
        [(_ name expression)
            (def-observable 'name 'expression)]))

(define (def-reaction symbol reactants products rate delay)
    (let ((model (get-model))
          (rbuilder (clr-new ReactionInfo+ReactionBuilder (symbol->string symbol))))

        (for-each (lambda (r) (clr-call ReactionInfo+ReactionBuilder AddReactant rbuilder (clr-call ModelInfo GetSpeciesByName model (symbol->string r)))) reactants)
        (for-each (lambda (p) (clr-call ReactionInfo+ReactionBuilder AddProduct  rbuilder (clr-call ModelInfo GetSpeciesByName model (symbol->string p)))) products)

        (clr-call ReactionInfo+ReactionBuilder SetRate rbuilder (def-anon-expression rate))
        (if (not (null? delay)) (clr-call ReactionInfo+ReactionBuilder SetDelay rbuilder delay))
        (clr-call ModelInfo+ModelBuilder AddReaction *builder* (clr-call ReactionInfo+ReactionBuilder get_Reaction rbuilder))))

(define-syntax reaction
    (syntax-rules ()
        [(_ name reactants products rate)       (def-reaction 'name 'reactants 'products 'rate '())]
        [(_ name reactants products rate delay) (def-reaction 'name 'reactants 'products 'rate (def-anon-expression 'delay))]
    )
)

(define-syntax json
    (syntax-rules ()
        [(_ symbol filename)
            (begin
                ; open/parse the json file
                (clr-using compartments)
                (define handle (clr-new Configuration filename))
                ; define a new function based on 'symbol' to access json elements
                (define (symbol path)
                    (cond
                        ((string? path) (clr-call Configuration+Parameter AsDouble (clr-call Configuration get_Item handle path)))
                        ((symbol? path) handle)
                    )
                )
            )
        ]
        [(_ symbol node element)
            (begin
                (clr-using compartments)
                (define handle (clr-call Configuration+Parameter AsConfiguration (clr-call Configuration get_Item (node 'handle) element)))
                (define (symbol path)
                    (cond
                        ((string? path) (clr-call Configuration+Parameter AsDouble (clr-call Configuration get_Item handle path)))
                        ((symbol? path) (handle))
                    )
                )
            )
        ]
    )
)

(define (config path)
    (let ((cfg (clr-static-call Configuration get_CurrentConfiguration)))

        (clr-call Configuration+Parameter AsDouble (clr-call Configuration get_Item cfg path))
    )
)

) ; end library
